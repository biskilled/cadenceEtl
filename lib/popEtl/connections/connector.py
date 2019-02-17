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

from popEtl.config import config
from popEtl.glob.loaderFunctions import *
from popEtl.glob.glob import p

from popEtl.connections.db     import cnDb
from popEtl.connections.file   import cnFile


class connector ():
    def __init__ (self, connProp, connUrl=None, isSql=False):
        self.objClass   = None
        self.cIsSql     = isSql
        self.cWhere     = None

        # connType    = connProp[0].lower()
        connType = ''.join([i for i in connProp[0].lower() if not i.isdigit()])
        self.cType = connType
        self.cName = connProp[1]
        self.cUrl = connUrl if connUrl else config.CONN_URL[connProp[0].lower()]

        className   = eval ( config.CONNECTIONS_ACTIVE[connType] )
        if len(connProp)==3:    self.cWhere = connProp[2]

        if className:
                self.objClass   = className(self.cName, self.cType, self.cUrl, self.cIsSql, self.cWhere)
                self.cType      = self.objClass.cType
                self.cName      = self.objClass.cName
                self.cursor     = self.objClass.cursor
                self.conn       = self.objClass.conn
                self.cColumns   = self.objClass.cColumns
        else:
            p ("CONNECTOR->init: %s is Not valid connection .... quiting ...." %(connProp) ,"e")
            return

    # GENERAL
    def setColumns(self, sttDic):
        p ("CONNECTOR->setColumns: setColumn type:%s, name: %s " %(self.cType, self.cName), "ii")
        return self.objClass.setColumns(sttDic)

    def create (self, stt=None, seq=None,tblName=None):
        if seq:
            p ("CONNECTOR->create: create type:%s, name: %s WITH SEQUENCE: %s" % (self.cType , self.cName, str (seq)) , "ii")
        elif tblName:
            p("CONNECTOR->create: create new table type:%s, name: %s " % (self.cType, tblName), "ii")
        else:
            p ("CONNECTOR->create: create type:%s, name: %s " % (self.cType , self.cName) , "ii")
        self.objClass.create(stt=stt, seq=seq, tblName=tblName)

    def getColumns(self):
        p("CONNECTOR->getColumns: Get column strucure schema type:%s, name: %s " % (self.cType, self.cName), "ii")
        return self.objClass.getColumns()

    def structure (self,stt ,addSourceColumn=False,tableName=None, sqlQuery=None):
        p ("CONNECTOR->structure: Get current schema type:%s, name: %s " %(self.cType, self.cName) ,"ii")
        return self.objClass.structure(stt, addSourceColumn=addSourceColumn,tableName=tableName, sqlQuery=sqlQuery)

    def truncate (self):
        p ("CONNECTOR->truncate: Truncating schema type:%s, name: %s " %(self.cType, self.cName) ,"ii")
        return self.objClass.truncate()

    def execSP (self, sqlQuery):
        p ("CONNECTOR->execSP: schema:%s, name: %s, executing query %s " %(self.cType, self.cName,sqlQuery) ,"ii")
        return self.objClass.execSP (sqlQuery)

    def toDB(self, dst, stt=None):
        dstType = dst[0]
        dstName = dst[1]
        p("CONNECTOR->toDB: Transfer data from %s, type: %s to %s, type: %s " % (self.cName,self.cType, dstName, dstType), "ii")

        tarL  = []
        srcL  = []
        fnDic = {}

        if stt:
            for cnt, t in enumerate(stt):
                tarL.append (t)
                srcCol = stt[t]["s"] if "s" in stt[t] else "''"
                srcL.append (srcCol)
                if "f" in stt[t]:
                    fnc = eval(stt[t]["f"])
                    fnDic[cnt] = fnc if isinstance(fnc, (list, tuple)) else [fnc]
                # key is tuple of column: (c1,c2, c3 ...)
                # values is (location, string function, toEvel (true,false) )
                elif "c" in stt[t] or "ce" in stt[t]:
                    colList = stt[t]["c"][0]
                    colFun  = stt[t]["c"][1]
                    toEval  = True if "ce" in stt[t] else False
                    newKey  = []
                    for j, tc in enumerate(stt):
                        if tc in colList:
                            newKey.append ( j )
                    fnDic[tuple(newKey)] = (cnt, colFun, toEval)
        return self.objClass.toDB(dst=dst, tarL=tarL, srcL=srcL, fnDic=fnDic)

    def sqlTargetMapping(self):
        p("CONNECTOR->sqlTargetMapping: Update cColumns and cColumnsTDic, type %s, name: %s " % (self.cType,self.cName), "ii")
        return self.objClass.sqlTargetMapping()

    def allStrucure(self, filterDic=None, withType=False):
        p("CONNECTOR->allStrucure: Reciave all DB object, type %s, name: %s, filter %s, withType: %s  " % (self.cType, self.cName, str(filterDic), str(withType)), "ii")
        return self.objClass.allStrucure(filterDic, withType)


    def dfFromTable (self, columns=None, index_col=None):
        p("CONNECTOR->dfFromTable: Load into dataframe all data type:%s, name: %s " % (self.cType, self.cName), "ii")
        return self.objClass.dfFromTable (columns, index_col)

    def dfFromQuery (self, sql, index_col=None):
        p("CONNECTOR->dfFromQuery: SQL Query Load into dataframe all data type:%s, name: %s , query: %s" % (self.cType, self.cName, str(sql)), "ii")
        return self.objClass.dfFromQuery (sql, index_col)

    def minValues (self, colToFilter=None, resolution=None, periods=None, startDate=None):
        p("CONNECTOR->minValues: Return MINIMUM values of field %s data type:%s, name: %s " % (colToFilter, self.cType, self.cName), "ii")
        return self.objClass.minValues (colToFilter=colToFilter, resolution=resolution, periods=periods, startDate=startDate)

    def merge (self, mergeTable, mergeKeys=None):
        p("CONNECTOR->merge: type: %s, merge source %s with destination %s, keys: %s " % (self.cType, self.cName, str(mergeTable), str (mergeKeys)), "ii")
        return self.objClass.merge (mergeTable=mergeTable, mergeKeys=mergeKeys)

    def close (self):
        p ("CONNECTOR->close: CLOSING CONNECTION type:%s, name: %s " %(self.cType, self.cName) ,"ii")
        self.objClass.close()

    def cntRows (self):
        p ("CONNECTOR->cntRows: Count rows type:%s, name: %s " %(self.cType, self.cName) ,"ii")
        return self.objClass.cntRows()