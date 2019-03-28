# -*- coding: utf-8 -*-
# (c) 2017-2019, Tal Shany <tal.shany@biSkilled.com>
#
# This file is part of popEye
#
# popEye is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# popEye is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cadenceEtl.  If not, see <http://www.gnu.org/licenses/>.

import time
import sys
import os
import traceback

import multiprocessing.pool as mpool
from collections import OrderedDict

from popEtl.config import config
from popEtl.glob.glob import p, setQueryWithParams, decodeStrPython2Or3
from popEtl.glob.loaderFunctions import *
from popEtl.glob.enums import eDbType, eConnValues, isDbType
import popEtl.connections.dbQueries as queries
import popEtl.connections.dbQueryParser as queryParser

# Data sources
aConnection = [x.lower() for x in config.CONNECTIONS_ACTIVE]
if eDbType.SQL in aConnection or eDbType.ACCESS in aConnection :
    import pyodbc as odbc #   ceODBC as odbc #pyodbc  # pyodbc version: 3.0.7

if eDbType.MYSQL  in aConnection   :
    import pymysql as pymysql

if eDbType.VERTIVA in aConnection :
    import vertica_python
    # pip install vertica_python
    # Need to install pip install sqlalchemy-vertica-python as well !!!

if eDbType.ORACLE in aConnection  :
    import cx_Oracle                      # version : 6.1

class cnDb (object):
    def __init__ (self, connDic=None, connType=None, connName=None, connUrl=None, connFilter=None):
        self.cIsSql     = connDic [ eConnValues.connIsSql] if connDic else None
        self.cName      = setQueryWithParams ( connDic [ eConnValues.connObj] ) if connDic else connName
        self.cSchema    = None
        self.cType      = connDic [ eConnValues.connType] if connDic else connType

        if self.cIsSql:
            self.cSQL = self.cName
        elif self.cName:
            tblName = self.__wrapSql(col=self.cName, remove=False)
            self.cSQL = "SELECT * FROM "+tblName

        self.cColumns   = []
        # Will be update if there is a query as source and mapping in query as well (select x as yy.....
        self.cColumnsTDic= None
        self.cUrl       = connDic [ eConnValues.connUrl ] if connDic else connUrl
        self.cWhere     = connDic [ eConnValues.connFilter ] if connDic else connFilter
        self.cColoumnAs = True

        self.insertSql  = None

        if not self.cType or not isDbType(self.cType):
            p ("Connection type is not valid: %s, use connection from config file" %(str(self.cType)) )
            return
        if  not self.cUrl:
            p("Connection URL is not exists, use valid URL conn" )
            return

        p("db->init: DB type: %s, table: %s, url: %s" % (self.cType, self.cName, str(self.cUrl)), "ii")

        if eDbType.MYSQL == self.cType:
            self.conn = pymysql.connect(self.cUrl["host"], self.cUrl["user"], self.cUrl["passwd"], self.cUrl["db"])
            self.cursor = self.conn.cursor()
        elif eDbType.VERTIVA == self.cType:
            self.conn = vertica_python.connect(self.cUrl)
            self.cursor = self.conn.cursor()
        elif eDbType.ORACLE == self.cType:
            self.conn = cx_Oracle.connect(self.cUrl['user'], self.cUrl['pass'], self.cUrl['dsn'])
            if 'nls' in self.cUrl:
                os.environ["NLS_LANG"] = self.cUrl['nls']
            self.cursor = self.conn.cursor()
        elif eDbType.ACCESS == self.cType:
            self.conn       = odbc.connect (self.cUrl) # , ansi=True
            self.cursor     = self.conn.cursor()
            self.cColoumnAs = False
        else:
            self.conn = odbc.connect (self.cUrl) #ansi=True
            self.cursor = self.conn.cursor()

        if not self.cIsSql and self.cName:
            self.cName = self.__wrapSql(col=self.cName, remove=True)
            self.cName = self.cName.split(".")

            self.cSchema =self.cName[0] if len(self.cName) > 1 else config.DATA_TYPE['schema'][self.cType]
            self.cName =  self.cName[1] if len(self.cName) > 1 else self.cName[0]

            if self.cWhere and len (self.cWhere)>1:
                self.cWhere = re.sub (r'WHERE', '', self.cWhere, flags=re.IGNORECASE)
                self.cWhere = setQueryWithParams (self.cWhere)
                self.cSQL = self.cSQL + " WHERE " + self.cWhere

    def close(self):
        try:
            if self.cursor: self.cursor.close()
            if self.conn:   self.conn.close()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            p("sb->close: Exception :"+str(exc_type)+" file name:"+str(fname)+" line: "+str(exc_tb.tb_lineno)+" massage: "+str(exc_obj.message), "e")

    def setColumns(self, sttDic):
        ret = OrderedDict ()
        columnsList = [(i, sttDic[i]["t"]) for i in sttDic if "t" in sttDic[i]]

        dType = config.DATA_TYPE.keys()

        for tup in columnsList:
            fName = tup[0]
            fType = tup[1]

            fmatch = re.search ("\(.+\)",fType)

            if fmatch:
                fType = re.sub ("\(.+\)","",fType)

            if fType in dType:
                rType= config.DATA_TYPE[fType][self.cType]
                if (isinstance(rType, tuple )):
                    rType = rType[0]
            else:
                rType= config.DATA_TYPE['default'][self.cType]
                fmatch = None
            fullRType = str(rType)+""+str(fmatch.group()) if fmatch else rType

            self.cColumns.append ( (fName , fullRType.lower()) )
        p("db->setColumns: type: %s, table %s will be set with column: %s" %(self.cType,self.cName, str(self.cColumns) ), "ii")
        return

    def create(self, stt=None,  seq=None, tblName=None):
        tblName = tblName if tblName else "[" + self.cSchema + "].[" + self.cName+"]" if self.cSchema else "["+self.cName+"]"
        colList = [(t,stt[t]["t"]) for t in stt if "t" in stt[t]] if stt else self.getColumns()

        if colList and len (colList)>0:
            boolToCreate = self.__cloneObject(colList, tblName)

            col = "("
            # create new table
            if boolToCreate:
                sql = "CREATE TABLE "+tblName+" \n"
                if seq:
                    colSeqName = self._wrapSql(col=seq['column'], remove=True)
                    colType    = getattr(queries, self.cType + "_seq")(seq)
                    col += "["+colSeqName+"]"+"\t"+ colType
                for colTup in colList:
                    colName = colTup[0].replace("[","").replace("]","")
                    if colName != colTup[1]:
                        col += "["+colName+"]"+"\t"+ colTup[1] +",\n"
                col = col[:-2]
                col+=")"
                sql += col
                p ("Create table \n"+sql)
                self.__executeSQL (sql)
        else:
            p("db->create: Table %s cannot create - problem with mappong source columns, src column: %s " %( str(self.cName), str(colList) ), "e")

    def truncate(self, tbl=None):
        tbl = tbl if tbl else self.cName
        sql = getattr(queries, self.cType + "_truncate")(tbl)

        self.__executeSQL(sql)
        p("db->truncate: truncate table DB type: %s, table: %s, url: %s" % (self.cType, self.cName, str(self.cUrl)),"ii")

    def getColumns (self):
        if self.cColumns and len(self.cColumns)>0:
            return self.cColumns
        else:
            self.structure (stt=None)
        return self.cColumns

    def structure (self, stt, tableName=None, addSourceColumn=False, sqlQuery=None):
        tableStructure  = []
        # If there is query and there is internal maaping in query - will add this mapping to mappingColum dictionary
        if self.cIsSql:
            stt = self.__sqlQueryMapping (stt=stt, addSourceColumn=addSourceColumn, sqlQuery=sqlQuery)
            for t in stt:
                if "s" in  stt[t] and "t" in stt[t]:
                    tableStructure.append ( (stt[t]["s"] , stt[t]["t"]) )
        else:
            # Get closing and starting column
            sttTemp = OrderedDict()
            sttSource = {}
            #get all source from stt
            if stt:
                for t in stt:
                    if "s" in stt[t]:
                        if stt[t]["s"] not in sttSource:
                            sttSource[stt[t]["s"]] = t
                        else:
                            tmpList = sttSource[stt[t]["s"]] if isinstance(sttSource[stt[t]["s"]], list) else sttSource[stt[t]["s"]].split()
                            tmpList.append ( t )
                            sttSource[stt[t]["s"]] = tmpList


            tableName = tableName if tableName else self.cName
            if self.cType in ('access'):
                rows = self.__access (tableName)
            else:
                sql = getattr(queries, self.cType + "_columnDefinition")(tableName)
                self.__executeSQL(sql, commit=False)
                rows = self.cursor.fetchall()
            for row in rows:
                cName = row[0]
                cType = row[1].lower().replace(' ','')
                if addSourceColumn or stt is None:
                    tableStructure.append( ( cName,cType ) )
                else:
                    if unicode(cName) in sttSource:
                        tableStructure.append((cName, cType))
                if cName in sttSource:
                    targetKey  = sttSource[cName]
                    if isinstance(targetKey, list):
                        for tKey in targetKey:
                            val = stt[tKey]
                            if "t" not in val: val["t"] = cType
                            if tKey not in sttTemp: sttTemp[tKey] = val
                    else:
                        val = stt[targetKey]
                        if "t" not in val: val["t"] = cType
                        if targetKey not in sttTemp: sttTemp[targetKey] = val
                else:
                    targetKey   = cName
                    val         = {"s":cName,"t":cType}
                    if targetKey not in sttTemp:
                        if (stt is not None and addSourceColumn) or stt is None:
                            sttTemp[targetKey] = val

            if stt:
                for t in stt:
                    if t not in sttTemp: sttTemp[t] = stt[t]


            if len(sttTemp)>0: stt = sttTemp

        self.cColumns = tableStructure
        return stt

    def loadData(self, srcVsTar, results, numOfRows, cntColumn):
        if self.cIsSql:
            p("db->loadData: Object is query... connot load data, %s " %(self.cName))
            return

        if results and numOfRows>0:
            tarSQL = "INSERT INTO " + self.cName + " "
            if srcVsTar and len(srcVsTar)>0:
                tarL = [self.__wrapSql(col=t[1], remove=False, cType=self.cType) for t in srcVsTar]
                tarSQL += "(" + ','.join(tarL) + ") "
                tarSQL += "VALUES (" + ",".join(["?" for x in range(len(tarL))]) + ")"
            else:
                cntColumn = cntColumn if cntColumn else len (results[0])
                tarSQL += "VALUES (" + ",".join(["?" for x in range(cntColumn)]) + ")"

            try:
                self.cursor.executemany(tarSQL, results)
                self.conn.commit()
                p('db->loadData: Load %s into target: %s >>>>>> ' % (str(numOfRows), self.cName), "ii")
            except Exception as e:
                p("db->loadData: type: %s, name: %s ERROR in cursor.executemany !!!!" % (self.cType, str(self.cName)), "e")
                p("db->loadData: ERROR, target query: %s " % str(tarSQL), "e")
                p("db->loadData: ERROR, sample result: %s " % str(results[0]), "e")
                p(e, "e")

                if config.RESULT_LOOP_ON_ERROR:
                    p("db->loadData: ERROR, Loading row by row  ", "e")
                    iCnt = 0
                    tCnt = len (results)
                    for r in results:
                        try:
                            iCnt+=1
                            r = [r]
                            self.cursor.executemany(tarSQL, r)
                            self.conn.commit()
                        except Exception as e:
                            ret = ""
                            for col in r[0]:
                                if col is None:
                                    ret += str(col) + ","
                                elif str(col).replace(".", "").replace(",", "").isdigit():
                                    ret += str(col) + " ,"
                                else:
                                    ret += "'" + str(col) + "' ,"
                            p("db->loadData: ERROR, LOOPING ON ALL RESULTS, ROW ERROR ", "e")
                            p(e, "e")
                            p(tarSQL, "e")
                            p(ret, "e")
                    p("db->loadData: ERROR Row by row: loader %s out of %s  " %(str(iCnt),str(tCnt)) , "e")
        return

    def transferToTarget(self, dstObj, srcVsTar, fnDic, pp):
        srcSql = self.__dbMapSrcVsTarget(srcSql=self.cSQL, srcVsTar=srcVsTar)
        try:
            self.__executeSQL(str(srcSql), commit=False)
            columnsInSOurce     = [x[0] for x in self.cursor.description]
            totalColumnInSource = len(columnsInSOurce)

            p ('db->transferToTarget: Loading total columns:%s, object name: %s  ' %(str(totalColumnInSource), str(dstObj.cName)),"ii")
            self.__parallelProcessing (dstObj=dstObj, srcVsTar=srcVsTar, fnDic=fnDic, pp=pp,  cntColumn=totalColumnInSource)

        except Exception as e:
            p("db->transferToTarget: ERROR Exectuging query: %s, type: %s >>>>>>" % (srcSql, self.cType) , "e")
            p(str(e), "e")

    def __dbMapSrcVsTarget ( self,srcSql, srcVsTar ):
        # there is column mapping or function mapping
        if not srcVsTar or len(srcVsTar)==0:
            return srcSql

        stcSelect = srcSql.lower().replace("\n", " ").find("select ")
        stcFrom   = srcSql.lower().replace("\n", " ").find(" from ")

        if stcSelect > -1 and stcFrom > 0:
            preSrcSql = srcSql[:stcSelect + 7]
            postSrcSql= srcSql[stcFrom:]
            newCol    = ""
            for tup in srcVsTar:
                if self.cIsSql:
                    srcC = tup[0]
                else:
                    srcC = self.__wrapSql(col=tup[0], remove=False) if tup[0] != "''" else tup[0]

                srcT = self.__wrapSql(col=tup[1], remove=False)
                newCol += srcC + " AS " + srcT + "," if self.cColoumnAs else srcC + ","

            newCol = newCol[:-1]
            srcSql = preSrcSql + newCol + postSrcSql
            p("db->__dbMapSrcVsTarget: there is mapping, update to new sql query: %s " % (srcSql), "ii")
        return srcSql

    def __parallelProcessing (self, dstObj, srcVsTar, fnDic, pp, cntColumn=None):
        numOfRows = 0
        iCnt      = 0
        pool = mpool.ThreadPool(config.NUM_OF_LOADING_THREAD)

        'An iterator that uses fetchmany to keep memory usage down'
        while True:
            try:
                if pp:
                    results = self.cursor.fetchmany(config.RESULT_ARRAY_SIZE)
                else:
                    results = self.cursor.fetchall()
                results = self.__functionResultMapping( results, fnDic)
            except Exception as e:
                p("db->__parallelProcessing: type: %s, name: %s ERROR in cursor.fetchmany" %(self.cType, str(self.cName)), "e")
                p(str(e), "e")
                break
            if not results or len(results)<1:
                break
            numOfRows+=len(results)
            pool.apply_async(func=self.__parallelProcessingLoad,args=(dstObj, srcVsTar, results, numOfRows, cntColumn))
            if iCnt < config.NUM_OF_LOADING_THREAD:
                iCnt+=1
            else:
                pool.close()
                pool.join()
                pool = mpool.ThreadPool(config.NUM_OF_LOADING_THREAD)
                iCnt = 0
        if pool:
            pool.close()
            pool.join()

    def __parallelProcessingLoad (self, dstObj, srcVsTar, results, numOfRows, cntColumn=None):
        try:
            return dstObj.loadData (srcVsTar, results, numOfRows, cntColumn)
        except Exception as e:
            p(e,'e')
            traceback.print_exc()
            raise e

    def __functionResultMapping (self, results,fnDic):
        if fnDic and len(fnDic) > 0 and results:
            for cntRows, r in enumerate(results):
                r = list(r)
                for pos, fnList in fnDic.items():
                    if not isinstance(pos, tuple):
                        uColumn = r[pos]
                        for f in fnList:
                            uColumn = f.handler(uColumn)
                        r[pos] = uColumn
                    else:
                        fnPos = fnList[0]
                        fnStr = fnList[1]
                        fnEval = fnList[2]
                        newVal = [str(r[cr]).decode(config.FILE_DECODING) for cr in pos]
                        newValStr = unicode(fnStr).format(*newVal)
                        r[fnPos] = eval(newValStr) if fnEval else newValStr
                results[cntRows] = r
        return results

    def minValues (self, colToFilter, resolution=None, periods=None, startDate=None):
        # there is min value to
        sql = getattr(queries, self.cType + "_minValue")(self.cName, self.cSchema, resolution, periods, colToFilter, startDate)
        p ("db->minValues: exec query : %s" %(sql), "ii")
        self.__executeSQL(sql)
        minValue = self.cursor.fetchone()
        if minValue and len (minValue)>0:
            minValue = minValue[0]
        else:
            p ("db->minValues: ERROR Getting miniumum value sql: "+sql, "e")
            return None
        p("db->minValues: get minimum value for table %s, field %s, sql : %s" %(str( self.cType), str(colToFilter), str(sql)), "ii" )
        return minValue

    def execSP (self, sqlQuery ):
        self.__executeSQL( sqlQuery )

    def merge (self, mergeTable, mergeKeys, sourceTable=None ):
        self.__sqlMerge(mergeTable, mergeKeys,sourceTable=sourceTable)

    def cntRows (self):
        sql = ""
        if self.cIsSql:
            sql = "SELECT COUNT (*) FROM ("+self.cName+")"
        else:
            tblName = self.cName.split(".")
            tblName = tblName[0] if len(tblName)==1 else tblName[1]
            sql = "SELECT COUNT (*) FROM ["+tblName+"]"
        self.__executeSQL(sql, commit=False)
        rows = self.cursor.fetchall()
        res = rows[0][0] if len(rows)>0 and len (rows[0])>0 else 0
        return res

    def select (self, sql):
        self.__executeSQL(sql=sql, commit=False)
        return self.cursor.fetchall()

    def getExistColumns (self, tblName=None):
        existStrucute = []
        tblName = tblName if tblName else self.cName
        tblName = self.__wrapSql(col=tblName, remove=True)
        objectExists = self.__objectExists(objName=tblName)
        if (objectExists):
            p("db-> __cloneObject: Table %s is exist >>>>" % (tblName), "ii")

            # get all current strucute of existing table
            sql = getattr(queries, self.cType + "_columnDefinition")(tblName)
            self.__executeSQL(sql, commit=False)

            rows = self.cursor.fetchall()
            for row in rows:
                colName = self.__wrapSql(col=row[0], remove=False)
                colType = row[1].lower().replace(' ', '')
                existStrucute.append((colName, colType))
        return existStrucute

    def __chunker(self, seq, size):
        return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))

    def __cloneObject(self, colList, tblName=None):
        colList = [(str(self.__wrapSql(col=tup[0], remove=False) ),tup[1].lower().replace (" ","")) for tup in colList]
        tblName = tblName if tblName else  self.cName
        existStrucute = self.getExistColumns(tblName=tblName)

        if config.TABLE_HISTORY:
            p ("db-> __cloneObject: Table History is ON ...","ii")
            oldName     = None
            schemaEqual = True

            if len(existStrucute)>0:
                schemaEqual = True if existStrucute == colList  else False

                if not schemaEqual:
                    srcPost = config.DATA_TYPE['colFrame'][self.cType][1]
                    p("db-> __cloneObject: UPDATE TABLE OLD STRUCTURE : %s " % str(existStrucute))
                    p("db-> __cloneObject: OLD STRUCTURE : %s " %str(existStrucute))
                    p("db-> __cloneObject: NEW STRUCTURE : %s " % str(colList))

                    if tblName[-1]=="]":
                        oldName = "%s_%s]" %(tblName[:-1], str(time.strftime('%y%m%d')))
                    else:
                        oldName = "%s_%s" %(tblName, str (time.strftime('%y%m%d')))

                    if (self.__objectExists(objName=oldName)):
                        num = 0
                        while (self.__objectExists(objName=oldName)):
                            num += 1
                            if tblName[-1] == "]":
                                oldName = "%s_%s_%s]" % (tblName[:-1], str(time.strftime('%y%m%d')), str(num))
                            else:
                                oldName = "%s_%s_%s" % (tblName, str(time.strftime('%y%m%d')), str(num))
                            oldName = oldName[: oldName.rfind('_')] + "_" + str(num)
                    if oldName:
                        p ("db-> __cloneObject: Table History is ON and changed, table %s exists ... will rename to %s" %(str (tblName) , str(oldName) ), "ii")
                        oldName = oldName[oldName.find('.')+1:]
                        oldName = self.__wrapSql(col=oldName, remove=True)
                        tblName = self.__wrapSql(col=tblName, remove=True)
                        sql = getattr (queries, self.cType+"_renameTable")(tblName,oldName)

                        #sql = eval (self.objType+"_renameTable ("+self.objName+","+oldName+")")
                        p("db-> __cloneObject: rename table, sql: %s" % (str(sql)), "ii")
                        self.__executeSQL(sql)
                else:
                    p("db-> __cloneObject: No changes made in table %s >>>>>" % (tblName), "ii")
                    return False
        else:
            if len(existStrucute)>0:
                p("db-> __cloneObject: Table History is OFF, table exists, will drop table %s... " % (str(tblName)), "ii")
                sql = eval (self.cType+"_renameTable("+tblName+")")
                self.__executeSQL(sql)
                return True
            else:
                p("db-> __cloneObject: Table History is OFF, table not exists exists, will create table %s... " % (str(tblName)), "ii")
        return True

    def __objectExists (self, objName=None):
        objName = self.cName if not objName else objName
        sql = "Select OBJECT_ID('"+objName+"')"
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        if row[0]:
            p ("db-> __objectExists: table %s exists ..." %(str (objName)) , "ii")
            return True
        p ("db-> __objectExists: Table %s is not exists ..." %(str (objName)) , "ii")
        return False

    def __executeSQL(self, sql, commit=True):
        if not (isinstance(sql, (list,tuple))):
            sql = [sql]
        try:
            for s in sql:
                s = unicode(s)
                self.cursor.execute(s)  # if 'ceodbc' in odbc.__name__.lower() else self.conn.execute(s)
            if commit:
                self.conn.commit()          # if 'ceodbc' in odbc.__name__.lower() else self.cursor.commit()
            return True
        except Exception as e:
            if e.args:
                error = e.args
                msg = decodeStrPython2Or3 (error, un=False)
            else:
                msg = e
            p("db->__executeSQL: ERROR : ", "e")
            p(e, "e")
            p("db->__executeSQL: ERROR %s " % str(msg), "e")
            p("db->__executeSQL: ERROR SQL: %s " %(sql),"e" )
            return False

    def __schemaCompare (self, colList):
        if self.cColumns == colList:
            p('db-> __schemaCompare: table exists with same strucure as column list ... ', "ii")

            tableStructure = self.structure()
            p('db-> __schemaCompare: table %s, old structure: %s, new: %s' %( str(self.cName), str(tableStructure), str(self.cColumns)), "ii")
            if set (self.cColumns) == set (tableStructure):
                p('db-> __schemaCompare: table %s has no change >>>' %(self.cType), "ii")
                return True
        p ('db-> __schemaCompare: table %s structure changed, old: %s, new: %s >>>>' %(self.cName, str(self.cColumns), str(colList) ), "ii")
        return False

    def __sqlMerge(self, mergeTable, mergeKeys,sourceTable):
        dstTable = self.__wrapSql(col=mergeTable, remove=False)

        if sourceTable:
            columns = self.getExistColumns(tblName=sourceTable)
            srcCol = [c[0] for c in columns]
        else:
            srcTable = self.__wrapSql(col=self.cName, remove=False)
            if self.cSchema:
                srcTable = "%s.%s" % (self.__wrapSql(col=self.cSchema, remove=False), srcTable)

            self.cColumns = self.getColumns()
            srcCol = [c[0] for c in self.cColumns]

        trgCol = srcCol
        # test
        colList     = []
        colFullList = []
        colOnList   = []
        for c in srcCol:
            if c in trgCol:
                colFullList.append(c)
                if c not in mergeKeys:
                    colList.append(c)
                else:
                    colOnList.append(c)

        notValidColumn = list(set(mergeKeys)-set(colOnList))
        if notValidColumn and len (notValidColumn)>0:
            p ("db->__sqlMerge: Not valid column %s " %(str (notValidColumn) ) , "ii")

        if len (colOnList)<1:
            mergeKeys = colList

        # dstTable, srcTable, mergeKeys, colList , colFullList
        colList = [self.__wrapSql(col=x, remove=False)  for x in colList]
        colFullList = [self.__wrapSql(col=x, remove=False)  for x in colFullList]
        sql = getattr(queries, self.cType + "_merge")(dstTable, srcTable, mergeKeys, colList , colFullList)
        self.__executeSQL(sql)
        p("db->sqlServer_Merge: Merged source %s table with %s table as target" % (srcTable, dstTable), "ii")

    def __sqlQueryMappingHelp (self,allTableStrucure, col):
        boolFind    = False
        colType     = None
        colTbl      = None
        colName     = None
        #colList     = col.split(".")
        #if len(colList) == 2:
        #    tblName = colList[0]
        #    colNameL = colList[1].lower()
        #else:
        tblName = None
        colNameL = col.lower()

        if tblName and tblName in allTableStrucure:
            if colNameL in allTableStrucure[tblName]:
                boolFind    = True
                colType     = allTableStrucure[tblName][colNameL][2]
                colTbl      = allTableStrucure[tblName][colNameL][1]
                colName     = allTableStrucure[tblName][colNameL][0]
            else:
                columnsName = allTableStrucure[tblName].keys()
                for colOrg in columnsName:
                    if colOrg in colNameL:
                        boolFind = True
                        colType = allTableStrucure[tblName][colOrg][2]
                        colTbl = allTableStrucure[tblName][colOrg][1]
                        colName = colNameL
                        break

        elif not tblName:
            for tblName in allTableStrucure:
                if colNameL in allTableStrucure[tblName]:
                    boolFind = True
                    colType = allTableStrucure[tblName][colNameL][2]
                    colTbl  = allTableStrucure[tblName][colNameL][1]
                    colName = allTableStrucure[tblName][colNameL][0]
                    break
                else:
                    columnsName = allTableStrucure[tblName].keys()
                    for colOrg in columnsName:
                        if colOrg in colNameL:
                            boolFind = True
                            colType = allTableStrucure[tblName][colOrg][2]
                            colTbl  = allTableStrucure[tblName][colOrg][1]
                            colName = colNameL
                            break
        if not boolFind:
            p("db->_sqlQueryMappingHelp there is column mapping which is not exists in any source table, ignoring. column: %s, tables: %s " % (str(col), str(allTableStrucure.keys())), "ii")
        return colType, colTbl, colName

    def __sqlQueryMapping (self,stt=None, addSourceColumn=False, sqlQuery=None):
        tableStructure  = []
        mappingDic      = {}
        sqlQ            = sqlQuery if sqlQuery else self.cName if self.cIsSql else None
        sttTemp         = None

        if sqlQ and len(sqlQ)>0:
            sttTemp             = OrderedDict()
            # sqlQ                = sqlQ.replace ("'",'"')
            columnTblDic        = queryParser.extract_tableAndColumns(sqlQ)

            allColumnsList      = [x for x in columnTblDic[config.QUERY_ALL_COLUMNS_KEY]]
            allColumnsTarget    = [x for x in columnTblDic[config.QUERY_TARGET_COLUMNS]]
            alldistinctColumn   = []
            allTableStrucure    = {}

            # Update alldistinctColumn
            for col in allColumnsList:
                colSplit = col.split(".",1)

                alldistinctColumn.append ( ('',colSplit[0]) if len(colSplit)==1 else (colSplit[0],colSplit[1]) )

            # update allTableStrucure dictionary : {tblName:{col name : ([original col name] , [tbl name] , [col structure])}}
            for tbl in columnTblDic:
                if tbl not in config.QUERY_ALL_COLUMNS_KEY:
                    fullTableName                   = tbl
                    allTableStrucure[tbl.lower()]   = {}
                    if 'schema' in columnTblDic[tbl] and columnTblDic[tbl]['schema'] and len (columnTblDic[tbl]['schema'])>0:
                        fullTableName = columnTblDic[tbl]['schema']+"."+tbl

                    sql = getattr(queries, self.cType + "_columnDefinition")(fullTableName)
                    self.__executeSQL(str (sql), commit=False )

                    for row in self.cursor.fetchall():
                        allTableStrucure[tbl.lower()][row[0].lower()] = ( decodeStrPython2Or3 (row[0], un=True), decodeStrPython2Or3 (tbl, un=True), decodeStrPython2Or3 (row[1].lower().strip().replace(' ', ''), un=True)  )

            # Create source mapping -> tableStructure
            # update mappingDic if there is column mapping

            for i, col in enumerate( alldistinctColumn ):
                targetName = allColumnsTarget[i]
                colType, colTbl, colName = self.__sqlQueryMappingHelp (allTableStrucure, col[1])
                if colName:
                    fullColName = unicode(colName + u"_" + colTbl) if alldistinctColumn.count(colName) > 1 else unicode(colName)
                    if len(col[0])>0:
                        fullColName = col[0]+"."+fullColName
                        colName = col[0]+"."+colName
                    tableStructure.append((unicode(fullColName), colType))
                    # update stt dictionary, if there is a mapping frorm query
                    sttTemp[targetName] = {"s":colName,"t":colType}

            # there is query with * - will add all columns

            if len (alldistinctColumn)<1:
                for tblName in allTableStrucure:
                    if tblName not in [config.QUERY_ALL_COLUMNS_KEY, config.QUERY_SEQ_TAG_VALUE, config.QUERY_SEQ_TAG_FIELD, config.QUERY_TARGET_COLUMNS]:
                        for colTup in allTableStrucure[tblName]:
                            if len (allTableStrucure[tblName][colTup])==3:
                                colName = allTableStrucure[tblName][colTup][0]
                                colType = allTableStrucure[tblName][colTup][2]
                                fullColName = tblName+"."+colName

                                tableStructure.append((unicode(fullColName), colType))
                                sttTemp[colName] = {"s": colName, "t": colType}

            self.cColumns = tableStructure

            for k in sttTemp:
                if stt and k in stt:
                    sttVal = stt[k]
                    if "s" not in sttVal:   sttVal["s"] = sttTemp[k]["s"]
                    if "t" not in sttVal:   sttVal["t"] = sttTemp[k]["t"]

                    sttTemp[k] = sttVal
            if stt:
                for k in stt:
                    if k not in sttTemp: sttTemp[k]=stt[k]
            #Sort stt by query mapping (order by sort if there is a use of more than one source column ....
            if sttTemp and len(sttTemp) > 0 and config.QUERY_SORT_BY_SOURCE:
                listSrc     = []
                listTar     = []
                sttTemp2    = OrderedDict()
                listItems   = sttTemp.items()
                for item in listItems:
                    listTar.append (item[0])
                    if "s" in item[1]:
                        listSrc.append ( item[1]["s"] )
                    else:
                        listSrc.append( None )

                for k in sttTemp:
                    if k not in sttTemp2:
                        sttTemp2[k] = sttTemp[k]
                        if "s" in sttTemp[k]:
                            src = sttTemp[k]["s"]
                            indices = [i for i,x in enumerate(listSrc) if x==src ]
                            if len(indices)>1:
                                for j in indices[1:]:
                                    addKey = listTar[j]
                                    sttTemp2[addKey] = sttTemp[addKey]
                sttTemp = sttTemp2

        sttTemp = sttTemp if sttTemp and len(sttTemp)>0 else None
        if not addSourceColumn and stt and len(stt)>0:
            sttTemp = stt
        return sttTemp

    def __wrapSql (self, col, remove=False, cType=None):
        if cType:
            srcPre, srcPost = config.DATA_TYPE['colFrame'][cType]
        else:
            srcPre, srcPost = config.DATA_TYPE['colFrame'][self.cType]
        coList = col.split(".")
        ret = ""
        for col in coList:
            col = col.replace(srcPre,"").replace(srcPost,"")
            if not remove:
                col= "%s%s%s" %(srcPre,col,srcPost)
            ret+=col+"."
        return ret[:-1]

    # Neeeds to support unicode values...
    def __access(self,tableName):
        ret = []
        for row in self.cursor.columns():
            if len(row)>3:
                curTblName = row[2]
                curTblName = curTblName.encode("utf-8")
                if curTblName == tableName:
                    colName = row.column_name.encode("utf-8")
                    colType = 'varchar(100)'
                    aType = row.type_name.lower()
                    if aType in ('varchar', 'longchar', 'bit','ntext'):
                        if row.column_size > 4098:
                            colType = 'varchar(max)'
                        else:
                            colType = 'varchar(' + str(row.column_size) + ')'
                    elif aType in ('integer', 'counter'):
                        colType = 'int'
                    elif aType in ('double'):
                        colType = 'float'
                    elif aType in ('decimal'):
                        colType = 'decimal(' + str(row.column_size) + "," + str(row.decimal_digits) + ")"
                    ret.append ( (colName , colType) )
        return ret
