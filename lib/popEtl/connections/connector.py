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

from collections import OrderedDict

from popEtl.config                  import config
from popEtl.glob.loaderFunctions    import *
from popEtl.glob.glob               import p
from popEtl.glob.enums              import eConnValues, eDbType

from popEtl.connections.db     import cnDb
from popEtl.connections.file   import cnFile

class connector ():
    def __init__ (self, connJsonVal=None, connType=None, connName=None,connObj=None, connFilter=None, connUrl=None,
                        extraConnVal=None, fileToLoad=None, isSql=False, isTarget=False, isSource=False):
        # connProp, connUrl=None, isSql=False, fileName=None
        # Expose all paramters into mapper and loader classes
        connDic = self._setDicConnValue(connJsonVal=connJsonVal, connType=connType, connName=connName,
                                        connObj=connObj, connFilter=connFilter, connUrl=connUrl,extraConnVal=extraConnVal,
                                        fileToLoad=fileToLoad,isSql=isSql, isTarget=isTarget, isSource=isSource )
        if connDic is None:
            p ("CONNECTOR->init: %s is Not valid connection .... quiting ...." %(str(connDic)) ,"e")
            return

        self.objClass   = None
        className   = eval ( config.CONNECTIONS_ACTIVE[connDic [eConnValues.connType] ] )

        if className:
            self.objClass   = className(connDic)
            self.cType      = self.objClass.cType
            self.cName      = self.objClass.cName
            self.cObj       = self.objClass.cObj
            self.cursor     = self.objClass.cursor
            self.conn       = self.objClass.conn
            self.cColumns   = self.objClass.cColumns
        else:
            p ("CONNECTOR->init: %s is Not valid connection .... quiting ...." %(str(connDic)) ,"e")
            return

    def connect (self):
        self.objClass.connect()

    def close (self):
        #p ("CONNECTOR->close: CLOSING CONNECTION type:%s, name: %s " %(self.cType, self.cName) ,"ii")
        self.objClass.close()

    def create (self, stt=None, seq=None,tblName=None):
        if self.objClass:
            objName = "query" if self.objClass.cIsSql else self.cObj
            if seq:
                p ("CONNECTOR->create: create type:%s, name: %s WITH SEQUENCE: %s" % (self.cType , objName, str (seq)) , "ii")
            elif tblName:
                p("CONNECTOR->create: create new table type:%s, name: %s " % (self.cType, tblName), "ii")
            else:
                p ("CONNECTOR->create: create type:%s, name: %s " % (self.cType , objName) , "ii")
        self.objClass.create(stt=stt, seq=seq, tblName=tblName)

    # GENERAL
    def setColumnsTypes (self, sttDic):
        columnsList = [(i, sttDic[i]["t"]) for i in sttDic if "t" in sttDic[i]]

        dType = config.DATA_TYPE.keys()

        for tup in columnsList:
            fName = tup[0]
            fType = tup[1]

            fmatch = re.search("\(.+\)", fType)

            if fmatch:
                fType = re.sub("\(.+\)", "", fType)

            if fType in dType:
                rType = config.DATA_TYPE[fType][self.cType]
                if (isinstance(rType, tuple)):
                    rType = rType[0]
            else:
                rType = config.DATA_TYPE['default'][self.cType]
                fmatch = None
            fullRType = str(rType) + "" + str(fmatch.group()) if fmatch else rType

            self.cColumns.append((fName, fullRType.lower()))
        p("db->setColumns: type: %s, table %s will be set with column: %s" % (
        self.cType, self.cName, str(self.cColumns)), "ii")
        return

    def getColumnsTypes(self):
        #p("CONNECTOR->getColumns: Get column strucure schema type:%s, name: %s " % (self.cType, self.cName), "ii")
        return self.objClass.getColumns()

    def structure (self,stt ,addSourceColumn=False,tableName=None, sqlQuery=None):
        #p ("CONNECTOR->structure: Get current schema type:%s, name: %s " %(self.cType, self.cName) ,"ii")
        return self.objClass.structure(stt, addSourceColumn=addSourceColumn,tableName=tableName, sqlQuery=sqlQuery)

    def truncate (self):
        #p ("CONNECTOR->truncate: Truncating schema type:%s, name: %s " %(self.cType, self.cName) ,"ii")
        return self.objClass.truncate()

    def execSP (self, sqlQuery):
        #p ("CONNECTOR->execSP: schema:%s, name: %s, executing query %s " %(self.cType, self.cName,sqlQuery) ,"ii")
        return self.objClass.execSP (sqlQuery)

    def transferToTarget(self, dstObj, sttDic):
        #p("CONNECTOR->transferToTarget: Transfer data from %s, type: %s to %s, type: %s " % (self.cName, self.cType, dstObj.cName, dstObj.cType), "ii")
        pp = False if dstObj.cType in [eDbType.FILE] else True
        srcVsTar= []
        fnDic   = {}

        if sttDic:
            for cnt, t in enumerate(sttDic):
                newMap = (sttDic[t]["s"] if "s" in sttDic[t] else "''",t,)
                srcVsTar.append (newMap)
                if "f" in sttDic[t]:
                    fnc = eval(sttDic[t]["f"])
                    fnDic[cnt] = fnc if isinstance(fnc, (list, tuple)) else [fnc]
                # key is tuple of column: (c1,c2, c3 ...)
                # values is (location, string function, toEvel (true,false) )
                elif "c" in sttDic[t] or "ce" in sttDic[t]:
                    colList = sttDic[t]["c"][0]
                    colFun  = sttDic[t]["c"][1]
                    toEval  = True if "ce" in sttDic[t] else False
                    newKey  = []
                    for j, tc in enumerate(sttDic):
                        if tc in colList:
                            newKey.append ( j )
                    fnDic[ tuple(newKey) ] = (cnt, colFun, toEval)
        return self.objClass.transferToTarget(dstObj=dstObj, srcVsTar=srcVsTar, fnDic=fnDic, pp=pp)

    def loadData(self, srcVsTar, results, numOfRows, cntColumn):
        return self.objClass.loadData(srcVsTar, results, numOfRows, cntColumn)

    def minValues (self, colToFilter=None, resolution=None, periods=None, startDate=None):
        #p("CONNECTOR->minValues: Return MINIMUM values of field %s data type:%s, name: %s " % (colToFilter, self.cType, self.cName), "ii")
        return self.objClass.minValues (colToFilter=colToFilter, resolution=resolution, periods=periods, startDate=startDate)

    def merge (self, mergeTable, mergeKeys=None):
        #p("CONNECTOR->merge: type: %s, merge source %s with destination %s, keys: %s " % (self.cType, self.cName, str(mergeTable), str (mergeKeys)), "ii")
        return self.objClass.merge (mergeTable=mergeTable, mergeKeys=mergeKeys)

    def cntRows (self):
        #p ("CONNECTOR->cntRows: Count rows type:%s, name: %s " %(self.cType, self.cName) ,"ii")
        return self.objClass.cntRows()

    def _setDicConnValue(self,  connJsonVal=None, connType=None, connName=None,connObj=None, connFilter=None, connUrl=None,
                                extraConnVal=None, fileToLoad=None,isSql=False, isTarget=False, isSource=False):

        retVal = {eConnValues.connName: connName,
                  eConnValues.connType: connType.lower() if connType else None,
                  eConnValues.connUrl: connUrl,
                  eConnValues.connUrlExParams: extraConnVal,
                  eConnValues.connObj: connObj,
                  eConnValues.connFilter: connFilter,
                  eConnValues.fileToLoad: fileToLoad,
                  eConnValues.connIsSql: isSql,
                  eConnValues.connIsSrc: isSource,
                  eConnValues.connIsTar: isTarget}

        if isinstance(connJsonVal, (tuple, list)):
            if len(connJsonVal) == 1:
                retVal[eConnValues.connName] = connJsonVal[0]
            elif len(connJsonVal) >= 2:
                retVal[eConnValues.connName] = connJsonVal[0]
                retVal[eConnValues.connObj] = connJsonVal[1]
                if retVal[eConnValues.connType] is None:
                    retVal[eConnValues.connType] = connJsonVal[0].lower()
                if len(connJsonVal) == 3:
                    retVal[eConnValues.connFilter] = connJsonVal[2]
            else:
                err = "glob->_setDicConnValue: Connection paramter is not valid, must have 1,2 or 3 params: %s " % (str(connJsonVal))
                p(err, "e")
                raise Exception(err)

            if retVal[eConnValues.connName] is None:
                err = "glob->_setDicConnValue: Connection Name is not defined: %s " % (connJsonVal)
                p(err, "e")
                raise Exception(err)

            if retVal[eConnValues.connUrl] is None:
                if retVal[eConnValues.connName] in config.CONN_URL:
                    connUrl = config.CONN_URL[retVal[eConnValues.connName]]
                    retVal[eConnValues.connUrl] = connUrl
                    if isinstance(connUrl, (dict, OrderedDict)):
                        if eConnValues.connType in connUrl:
                            retVal[eConnValues.connType] = connUrl[eConnValues.connType].lower()
                        if eConnValues.connUrl in connUrl:
                            retVal[eConnValues.connUrl] = connUrl[eConnValues.connUrl]
                        if eConnValues.fileToLoad in connUrl:
                            retVal[eConnValues.fileToLoad] = connUrl[eConnValues.fileToLoad]
                else:
                    err = "glob->_setDicConnValue: Connection Name %s is not defined in CONN_URL config. define names are : %s  " % (
                    retVal[eConnValues.connName], str(list(config.CONN_URL.keys())))
                    p(err, "e")
                    raise Exception(err)
            # remove number from connection type in case we used it in config.CONN_URL
            # sample : sql1 - will be rename to sql as a type
            retVal[eConnValues.connType] = ''.join([i for i in retVal[eConnValues.connType].lower() if not i.isdigit()])

            #################   ACCESS - ADD EXTRA PARAMTERS -> Access File DB
            if eDbType.ACCESS == retVal[eConnValues.connType]:
                if retVal[eConnValues.connUrlExParams] is not None:
                    retVal[eConnValues.connUrl] = retVal[eConnValues.connUrl][0] % (
                                retVal[eConnValues.connUrl][1] + str(
                            retVal[eConnValues.connUrlExParams].split(".")[0] + ".accdb"))
                else:
                    err = "glob->_setDicConnValue: Connection %s is missing Access file " % (
                    retVal[eConnValues.connName])
                    p(err, "e")
                    raise Exception(err)

            #################   LOAD SQL QUERIES FROM FILE - ADD EXTRA PARAMTERS -> File loacation
            foundQuery = False
            allParams = []
            if retVal[eConnValues.fileToLoad] is not None:
                sqlFile = "%s.sql" % retVal[eConnValues.fileToLoad] if retVal[eConnValues.fileToLoad][
                                                                       -4:] != ".sql" else retVal[
                    eConnValues.fileToLoad]
                if os.path.isfile(sqlFile):
                    with io.open(sqlFile, 'r', encoding=config.PARSER_FILE_ENCODE) as inp:
                        sqlScript = inp.readlines()
                        allQueries = queryParsetIntoList(sqlScript, getPython=True, removeContent=True, dicProp=None,
                                                         pythonWord=config.PARSER_SQL_MAIN_KEY)

                        for q in allQueries:
                            allParams.append(q[1])
                            if q[0] and q[0] == retVal[eConnValues.connObj]:
                                retVal[eConnValues.connObj] = q[1]
                                retVal[eConnValues.connIsSql] = True
                                foundQuery = True
                                break
                    if not foundQuery:
                        err = "glob->_setDicConnValue: There is paramter %s which is not found in %s, existing keys: %s " % (
                        retVal[eConnValues.connObj], sqlFile, str(allParams))
                        p(err, "e")
                        raise Exception(err)
                else:
                    err = "glob->_setDicConnValue: %s is not found  " % (sqlFile)
                    p(err, "e")
                    raise Exception(err)

            retVal[eConnValues.connType] = isDbType(retVal[eConnValues.connType])

            if retVal[eConnValues.connName] is not None and \
                    retVal[eConnValues.connType] is not None and \
                    retVal[eConnValues.connObj] is not None and \
                    retVal[eConnValues.connUrl] is not None:
                p("glob->_setDicConnValue: Connection params: %s " % (str(retVal)), "ii")
                return retVal

            err = "glob->_setDicConnValue: Connection params are not set: %s " % (str(retVal))
            p(err, "e")
            raise Exception(err)