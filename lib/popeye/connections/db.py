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
import re
from collections import OrderedDict
import multiprocessing.pool as mpool

from lib.popeye.config  import config, p, setQueryWithParams
import lib.popeye.connections.dbQueries as queries
import lib.popeye.connections.dbQueryParser as queryParser
from  lib.popeye.glob.globalFunctions import *


aConnection = [x.lower() for x in config.CONNECTIONS_ACTIVE]

if "sql" in aConnection or "access" in aConnection :
    #import pyodbc
    import ceODBC as odbc

if "mysql" in aConnection:
    import pymysql

if "vertica" in aConnection :
    # pip install vertica_python
    # Need to install pip install sqlalchemy-vertica-python as well !!!
    import vertica_python

if "oracle" in aConnection  :
    # version : 6.1
    import cx_Oracle



class cnDb (object):
    def __init__ (self, connObject, conType='sql', connUrl=None, isSql=False, connWhere=None):
        self.cIsSql     = isSql
        self.cName      = setQueryWithParams (connObject)
        self.cSchema    = None
        self.cType      = conType.lower()

        if self.cIsSql:
            self.cSQL = self.cName
        else:
            srcPre, srcPost = config.DATA_TYPE['colFrame'][self.cType]
            tblName = self.cName.split(".")
            if len(tblName) == 1:
                tblName = srcPre+tblName[0]+ srcPost
            else:
                tblName = srcPre + tblName[0] + srcPost + "." + srcPre + tblName[1] + srcPost
                #tblName = tblName[0] if len(tblName) == 1 else tblName[1]
            self.cSQL = "SELECT * FROM "+tblName


        self.cColumns   = []
        # Will be update if there is a query as source and mapping in query as well (select x as yy.....
        self.cColumnsTDic= None
        self.cUrl       = connUrl if connUrl else config.CONN_URL[self.cType]
        self.cWhere     = connWhere
        self.cColoumnAs = True

        p("db->init: DB type: %s, table: %s, url: %s" % (self.cType, self.cName, str(self.cUrl)), "ii")

        if 'mysql' in self.cType:
            self.conn = pymysql.connect(self.cUrl["host"], self.cUrl["user"], self.cUrl["passwd"], self.cUrl["db"])
            self.cursor = self.conn.cursor()
            self.cType = 'mysql'
        elif 'vertica' in conType.lower():
            self.conn = vertica_python.connect(self.cUrl)
            self.cursor = self.conn.cursor()
            self.cType = 'vertica'
        elif 'oracle' in conType.lower():
            self.conn = cx_Oracle.connect(self.cUrl['user'], self.cUrl['pass'], self.cUrl['dsn'])
            if 'nls' in self.cUrl:
                os.environ["NLS_LANG"] = self.cUrl['nls']
            self.cursor = self.conn.cursor()
            self.cType = 'oracle'
        elif 'access' in conType.lower():
            self.conn       = odbc.connect (self.cUrl) # , ansi=True
            self.cursor     = self.conn.cursor()
            self.cColoumnAs = False
            self.cType      = 'access'
        else:
            self.conn = odbc.connect (self.cUrl) #ansi=True
            self.cursor = self.conn.cursor()
            self.cType =  'sql'

        if not self.cIsSql:
            self.cSchema= self.cName[:self.cName.find(".")] if self.cName.find(".") > 0 else config.DATA_TYPE['schema'][self.cType]
            self.cName  = self.cName[self.cName.find(".") + 1:] if self.cName.find(".") > 0 else self.cName
            if self.cSchema:  self.cSchema.replace("[", "").replace("]", "")
            if self.cName:    self.cName.replace("[", "").replace("]", "")

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
            p("Exception :"+str(exc_type)+" file name:"+str(fname)+" line: "+str(exc_tb.tb_lineno)+" massage: "+str(exc_obj.message), "e")

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
                    colSeqName = seq['column'].replace("[","").replace("]","")
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

    def truncate(self):
        sql = getattr(queries, self.cType + "_truncate")(self.cName)

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
                    if str(cName, 'utf-8') in sttSource:
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

    def toTarget (self,  results, tarSQL, dst, fnDic, numOfRows):
        try:
            msgList = []

            targetObj = cnDb(dst[1], conType=dst[0])
            targetObj.cursor.executemany(tarSQL, results)
            targetObj.conn.commit()
            p('db->toTarget: FINISH Loading total of %s rows into target :%s ' % (str(numOfRows), str(dst[1])), "ii")
            targetObj.close()
        except Exception as e:
            p("db->toTarget: type: %s, name: %s ERROR in targetObj.cursor.executemany" % (self.cType, str(self.cName)), "e")
            p("db->toTarget: ERROR, target query: %s " % str(tarSQL), "e")
            p("db->toTarget: ERROR, sample result: %s " % str(results[0]), "e")
            p(str(e), "e")

            if targetObj and targetObj and config.RESULT_LOOP_ON_ERROR:
                p("db->toTarget: ERROR, Loading row by row  ", "e")

                iCnt = 0
                for r in results:
                    try:
                        iCnt+=1
                        #print iCnt
                        r = [r]
                        targetObj.cursor.executemany(tarSQL, r)
                        targetObj.conn.commit()
                    except Exception as e:
                        ret = ""
                        for col in r[0]:
                            if col is None:
                                ret += str(col) + ","
                            elif str(col).replace(".", "").replace(",", "").isdigit():
                                ret += str(col) + " ,"
                            else:
                                ret += "'" + str(col) + "' ,"
                        p("db->toTarget: ERROR, LOOPING ON ALL RESULTS, ROW ERROR ", "e")
                        p(str(e), "e")
                        p(tarSQL, "e")
                        p(ret, "e")
                targetObj.close()
        return

    def dbIter(self, tarSQL, dst, fnDic):
        numOfRows = 0
        iCnt      = 0
        pool = mpool.ThreadPool(config.NUM_OF_LOADING_THREAD)
        'An iterator that uses fetchmany to keep memory usage down'
        while True:
            try:
                results = self.cursor.fetchmany(config.RESULT_ARRAY_SIZE)
                if fnDic and len(fnDic) > 0:
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
                                newValStr = str(fnStr, 'utf-8').format(*newVal)
                                r[fnPos] = eval(newValStr) if fnEval else newValStr
                        results[cntRows] = r
            except Exception as e:
                p("db->doIter: type: %s, name: %s ERROR in cursor.fetchmany" %(self.cType, str(self.cName)), "e")
                p(str(e), "e")
                break
            if not results or len(results)<1:
                break
            numOfRows+=len(results)
            p('db->Iter: Loading total of %s rows , target :%s ' % (str(numOfRows), str(dst[1])), "ii")
            pool.apply_async(func=self.toTarget,args=(results, tarSQL, dst, fnDic, numOfRows))  #callback=log_result
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

    def toDB (self, dst, tarL, srcL, fnDic):
        srcSql  = self.cSQL

        TargetTableType = dst[0]
        TargetTableName = dst[1]
        tarSQL  = "INSERT INTO "+TargetTableName+" "

        # there is column mapping or function mapping
        if len (tarL)>0:
            tarPre, tarPost = config.DATA_TYPE['colFrame'][TargetTableType]
            srcPre, srcPost = config.DATA_TYPE['colFrame'][self.cType]
            stcSelect= srcSql.lower().find("select ")
            stcFrom  = srcSql.lower().find(" from ")

            if stcSelect>-1 and stcFrom>0:
                preSrcSql   = srcSql[:stcSelect+7]
                postSrcSql  = srcSql[stcFrom:]
                newCol = ""
                for i,t in enumerate(tarL):
                    srcCBasic  = srcL[i].split(".")
                    if self.cIsSql:
                        srcC =srcL[i]
                    else:
                        if len(srcCBasic)>1:
                            srcC =  srcCBasic[0]+"."+ srcPre + srcCBasic[1] + srcPost if srcL[i] != "''" else srcL[i]
                        else:
                            srcC = srcPre + srcCBasic[0] + srcPost if srcL[i] != "''" else srcL[i]

                    srcT = srcPre + t + srcPost
                    newCol += srcC + " AS " + srcT + "," if self.cColoumnAs else srcC + ","

                newCol = newCol[:-1]
                srcSql = preSrcSql + newCol + postSrcSql
                p("db->toDB: there is mapping, update to new sql query: %s " % (srcSql), "ii")


            tarL = [tarPre + t + tarPost for t in tarL]
            tarSQL +=  "(" + ','.join(tarL) + ") "
            tarSQL += "VALUES (" + ",".join(["?" for x in range(len(tarL))]) + ")"

        try:
            self.__executeSQL(str(srcSql), commit=False)
            p ('db->toDB: Loading total rows: %s, Excecuting sql %s ' %(str (self.cursor.rowcount), str (srcSql)),"ii")
            columnsInSOurce = [x[0] for x in self.cursor.description]
            totalColumnInSource = len(columnsInSOurce)

            if len (tarL)<1:
                tarSQL += "VALUES (" + ",".join(["?" for x in range(totalColumnInSource)]) + ")"

            self.dbIter(tarSQL=tarSQL, dst=dst, fnDic=fnDic)

        except Exception as e:
            p("db->toDB: ERROR Exectuging query: %s, type: %s >>>>>>" % (srcSql, self.cType) , "e")
            p(str(e), "e")

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
        self.__executeSQL( sqlQuery, direct=True )
        # print sqlQuery

    def merge (self, mergeTable, mergeKeys ):
        targetName      = mergeTable[mergeTable.find(".")+1:] if mergeTable.find(".")>0 else mergeTable
        targetSchema    = mergeTable[:mergeTable.find(".")] if mergeTable.find(".")>0 else None
        if targetName   : targetName.replace ("[","").replace ("]","")
        if targetSchema : targetSchema.replace ("[","").replace ("]","")

        self.__sqlMerge(targetName, targetSchema, mergeKeys)

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

    def __chunker(self, seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    def __cloneObject(self, colList, tblName=None):
        existStrucute = []
        tblName = tblName if tblName else  self.cName
        tblName = tblName.replace("[","").replace("]","")
        objectExists = self.__objectExists(objName=tblName)
        if (objectExists):
            p("db-> __cloneObject: Table %s is exist >>>>" % (tblName), "ii")

            #get all current strucute of existing table
            sql = getattr(queries, self.cType + "_columnDefinition")(tblName)
            self.__executeSQL(sql, commit=False)

            rows = self.cursor.fetchall()
            for row in rows:
                existStrucute.append((row[0], row[1].lower().replace(' ', '')))

        if config.TABLE_HISTORY:
            p ("db-> __cloneObject: Table History is ON ...","ii")
            oldName     = None
            schemaEqual = True

            if (objectExists):
                existStrucute   = [(str(tup[0]),tup[1].lower().replace (" ","")) for tup in existStrucute]
                colList         = [(str(tup[0]),tup[1].lower().replace (" ","")) for tup in colList]
                schemaEqual = True if existStrucute == colList  else False

                if not schemaEqual:
                    p("db-> __cloneObject: UPDATE TABLE OLD STRUCTURE : %s " % str(existStrucute))
                    p("db-> __cloneObject: OLD STRUCTURE : %s " %str(existStrucute))
                    p("db-> __cloneObject: NEW STRUCTURE : %s " % str(colList))
                    oldName = tblName+"_"+str (time.strftime('%y%m%d'))
                    if (self.__objectExists(objName=oldName)):
                        num = 1
                        if oldName[-1]=="]":
                            oldName = oldName[:-1] + "_" + str(num)+"]"
                        else:
                            oldName=oldName+"_"+str (num)
                        while (self.__objectExists(objName=oldName)):
                            num += 1
                            oldName = oldName[: oldName.rfind('_')] + "_" + str(num)
                    if oldName:
                        p ("db-> __cloneObject: Table History is ON and changed, table %s exists ... will rename to %s" %(str (tblName) , str(oldName) ), "ii")
                        oldName = oldName[oldName.find('.')+1:]
                        sql = getattr (queries, self.cType+"_renameTable")(tblName,oldName)

                        #sql = eval (self.objType+"_renameTable ("+self.objName+","+oldName+")")
                        p("db-> __cloneObject: rename table, sql: %s" % (str(sql)), "ii")
                        self.__executeSQL(sql)
                else:
                    p("db-> __cloneObject: No changes made in table %s >>>>>" % (tblName), "ii")
                    return False
        else:
            if (objectExists):
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

    def __executeSQL(self, sql, commit=True, direct=False):
        try:
            if (isinstance(sql, (list,tuple))):
                for s in sql:
                    if direct:
                        #self.conn.autocommit = True
                        self.cursor.execdirect(s)
                        #self.conn.autocommit = False
                    else:
                        self.cursor.execute(s)
            else:
                if direct:
                    #self.conn.autocommit = True
                    self.cursor.execdirect(sql)
                    #self.conn.autocommit = False
                else:
                    self.cursor.execute(sql)
            if commit:
                self.conn.commit()
            return True
        except  Exception as e:
            p("db->__executeSQL: ERROR : ")
            p(u"db->__executeSQL: ERROR \n: %s " % str(e,'utf-8'), "e")
            p ("db->__executeSQL: ERROR SQL: %s " %(sql),"e" )
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

    def __sqlMerge(self, targetTable, targetSchema, mergeKeys):
        srcCol = [c[0] for c in self.cColumns]
        trgCol = srcCol

        dstTable = "["+targetSchema+"].["+targetTable+"]" if targetSchema else "["+targetTable+"]"
        srcTable = "["+self.cSchema+"].["+self.cName+"]" if self.cSchema else "["+self.cName+"]"

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
        sql = getattr(queries, self.cType + "_merge")(dstTable, srcTable, mergeKeys, colList , colFullList)
        # print sql
        self.__executeSQL(sql)
        p("db->sqlServer_Merge: Merged source %s table with %s table as target" % (srcTable, dstTable), "ii")

    def __sqlQueryMappingHelp (self,allTableStrucure, col):
        boolFind    = False
        colType     = None
        colTbl      = None
        colName     = None
        colList     = col.split(".")
        if len(colList) == 2:
            tblName = colList[0]
            colNameL = colList[1].lower()
        else:
            tblName = None
            colNameL = colList[0].lower()

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
                colSplit = col.split(".")
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
                        allTableStrucure[tbl.lower()][row[0].lower()] = ( unicode (row[0]), unicode(tbl),  unicode (row[1].lower().strip().replace(' ', '')) )

            # Create source mapping -> tableStructure
            # update mappingDic if there is column mapping

            for i , col in enumerate(alldistinctColumn):
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
