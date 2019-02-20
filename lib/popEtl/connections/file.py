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

from __future__ import  (absolute_import, division, print_function)
__metaclass__ = type

import collections
import os
import shutil
import time
import csv
import io
import pandas as pd

from popEtl.config          import config
from popEtl.glob.glob       import p
from popEtl.glob.enums      import eConnValues
from popEtl.connections.db  import cnDb

class cnFile ():
    def __init__ (self, connDic):

        self.cName      = connDic [ eConnValues.connObj ]
        self.cType      = connDic [ eConnValues.connType ]
        self.columns    = []
        self.cUrl       = connDic [ eConnValues.connUrl ]
        self.cursor     = None
        self.conn       = None
        self.cColumns   = None

        self.header     = None
        self.fnDic      = None

        connProp = self.cUrl.keys()
        self.fileDelimiter  = self.cUrl['delimiter'] if 'delimiter' in connProp else config.FILE_DEFAULT_DELIMITER
        self.fileHeader     = self.cUrl['header'] if 'header' in connProp else config.FILE_DEFAULT_HEADER
        self.folderPath     = self.cUrl['folder'] if 'folder' in connProp else config.FILE_DEFAULT_FOLDER
        self.fullPath       = os.path.join(self.folderPath, self.cName)
        self.newLine        = self.cUrl['newLine'] if 'newLine' in connProp else config.FILE_DEFAULT_NEWLINE
        self.encoding       = self.cUrl['encoding'] if 'encoding' in connProp else config.FILE_DECODING
        self.errors         = self.cUrl['errors'] if 'errors' in connProp else config.FILE_LOAD_WITH_CHAR_ERR


        p ("file-> init: Delimiter %s, Header %s, Root dir: %s, File: %s " %(str(self.fileDelimiter) , str(self.fileHeader), str(self.folderPath), self.cName ), "ii")

    def close (self):
        pass

    def getColumns (self):
        if self.cColumns and len(self.cColumns)>0:
            return self.cColumns
        else:
            self.structure (stt=None)
        return self.cColumns

    def setColumns(self, colList):
        columnsList = []
        ret = []
        # check if column object is ordered dictionay
        if len (colList) == 1 and isinstance( colList[0] , collections.OrderedDict ):
            columnsList = colList[0].items()
        else:
            if isinstance( colList, list) and len (colList)>0:
                columnsList = colList
            else:
                if isinstance( colList, (dict, collections.OrderedDict) ):
                    columnsList = colList.items()
                else:
                    p ("file->setColumns: List of column is not ordered dictioany or list or regualr dictioanry ....","e")
                    return None

        for col in columnsList:
            if (isinstance (col, (tuple, list))):
                colName = col[0]
            else:
                colName = col
            ret.append(colName)
        self.columns = ret

        p("file-> setColumns: type: %s, file %s will be set with column: %s" % (self.cType, self.cName, str(self.columns)), "ii")
        return self.columns

    def create(self, colList, fullPath=None,  seq=None):
        fullPath = fullPath if fullPath else self.fullPath

        if seq:
            p ("file->create: FILE %s, Sequence is not activated in target file connection, seq: %s  ..." %(str(fullPath) , str (seq) ), "e")
        self.__cloneObject()
        if self.fileHeader:
            p ("file->create: FILE %s, using columns %s as hedaers ..." %(str(fullPath) , str(self.fileHeader) ), "ii")
        else:
            p ("file->create: FILE %s, using columns %s as hedaers ..." %(str(fullPath) , str(colList) ) , "ii")

        # create new File
        self.fileObj = open (fullPath, 'w')

    def structure(self, stt ,addSourceColumn=False,tableName=None, sqlQuery=None):
        stt = collections.OrderedDict() if not stt else stt
        addToStt = False
        if (os.path.isfile(self.fullPath)):
            retWithHeaders  = []
            retNoHeaders    = []
            p ('file->structure: file %s exists, delimiter %s, will extract column structure' %( self.fullPath, str(self.fileDelimiter) ), "ii")
            with io.open(self.fullPath, 'r', encoding=config.FILE_DECODING) as f:
                headers = f.readline().strip(config.FILE_DEFAULT_NEWLINE).split(self.fileDelimiter)

            if len(headers)>0:
                defDataType = config.DATA_TYPE['default'][self.cType]
                defColName =  config.FILE_DEF_COLUMN_PREF
                sttSource = {}
                if len(stt)>0:
                    for t in stt:
                        if "s" in stt[t]:
                            if stt[t]["s"] not in sttSource:
                                sttSource[stt[t]["s"]] = config.DATA_TYPE['default'][self.cType]
                                if "t" in stt[t]:
                                    sttSource[stt[t]["s"]] = stt[t]["t"]
                            else:
                                if "t" in stt[t]:
                                    sttSource[stt[t]["s"]] = stt[t]["t"]
                        if "t" not in stt[t]:
                            stt[t]["t"] = config.DATA_TYPE['default'][self.cType]
                else:
                    addToStt = True

                for i , col in enumerate (headers):
                    cName = col if self.fileHeader else config.FILE_DEF_COLUMN_PREF+str(i)
                    cType = config.DATA_TYPE['default'][self.cType]
                    if col in sttSource:
                        cType = sttSource[col]

                    if addSourceColumn or addToStt:
                        if col not in sttSource:
                            stt[cName] = {"s":cName, "t":cType}

                    retWithHeaders.append( (cName , cType) )

                self.cColumns = retWithHeaders
                if (self.fileHeader):
                    p ('file->structure: file %s contain header will use default %s as data type for each field >>> ' %( self.fullPath, str(defDataType) ), "ii")
                else:
                    p ('file->structure: file %s come without headers, will use prefix name %s and default %s as data type for each field >>> ' %( self.fullPath, str(defColName), str(defDataType) ), "ii")
            else:
                p ('file->structure: file %s is empty, there is no mapping to send >>> ' %( str(self.fullPath) ), "ii")
        else:
            p('file->structure: file %s is not exists >>> ' % (str(self.fullPath)), "ii")

        return stt

    def _updateRow (self, row ):
        def rep (s):
            return s.replace('"','').replace ("\t","")
        ret = row
        ret = [rep(row[c]) if str(c).isdigit() and len(row[c])>0 else None for c in self.header]
        if self.fnDic:
            lenR = len (ret)
            for pos, fnList in self.fnDic.items():
                if not isinstance(pos, tuple):
                    uColumn = ret[pos] if lenR<pos else None
                    for f in fnList:
                        uColumn = f.handler(uColumn)
                    if lenR<=pos:
                        ret.append(uColumn)
                    else:
                        ret[pos] = uColumn
                else:
                    fnPos = fnList[0]
                    fnStr = fnList[1]
                    fnEval = fnList[2]
                    newVal = [str(ret[cr]).decode(config.FILE_DECODING) for cr in pos]
                    newValStr = str(fnStr,'utf-8').format(*newVal)
                    if lenR<=pos:
                        ret.append( eval(newValStr) if fnEval else newValStr )
                    else:
                        ret[fnPos] = eval(newValStr) if fnEval else newValStr
        return ret

    def toDB (self, dst, tarL, srcL, fnDic):
        self.fnDic = fnDic
        TargetTableType = dst[0]
        TargetTableName = dst[1]
        split_line = None
        tarSQL  = "INSERT INTO "+TargetTableName+" "

        try:
            # there is column mapping or function mapping
            if len (tarL)>0:
                tarPre, tarPost = config.DATA_TYPE['colFrame'][TargetTableType]

                tarL = [tarPre + t + tarPost for t in tarL]
                tarSQL +=  "(" + ','.join(tarL) + ") "
                tarSQL += "VALUES (" + ",".join(["?" for x in range(len(tarL))]) + ")"

            dataArr = []
            if not self.fileHeader:
                self.header = []
                for i , col in enumerate(srcL):
                    col = col.replace (config.FILE_DEF_COLUMN_PREF, "")
                    if col.isdigit():
                        self.header.append (int(col))
                    else:
                        self.header.append(i)
            with io.open (self.fullPath, 'r', encoding=self.encoding, errors=self.errors) as fFile: # encoding='windows-1255' encoding='utf8'
            #    #textFile = csv.reader(fFile, delimiter=self.fileDelimiter, quotechar="'", quoting=csv.QUOTE_NONNUMERIC)
                for i, line in enumerate(fFile):
                    line = line.strip(config.FILE_DEFAULT_NEWLINE)
                    split_line = line.split(self.fileDelimiter)
                    if self.fileHeader and i==0:
                        self.header = []
                        split_line = [c.strip() for c in split_line]
                        if len (srcL)>0:
                            for i, sCol in enumerate(srcL):
                                if sCol.strip() in split_line:
                                    self.header.append (split_line.index(sCol))
                                elif sCol == "''":
                                    self.header.append(sCol)
                                else:
                                    p ("file->toDB: Loading %s, column %s mapped but not found in file headers, ignoring %s ..." %(str(self.fullPath), str(sCol), str(split_line)))
                        continue

                    split_line = self._updateRow(split_line)
                    dataArr.append(split_line)
                    if config.FILE_MAX_LINES_PARSE>0 and i>0 and i%config.FILE_MAX_LINES_PARSE == 0:
                        self.toTarget(dataArr, tarSQL, dst, fnDic, i)
                        dataArr = list ([])
                if len(dataArr)>0 : #and split_line:
                    self.toTarget(dataArr, tarSQL, dst, fnDic, i)

        except Exception as e:
            p("db->toDB: ERROR loading file: %s, type: %s >>>>>>" % (self.cName, self.cType) , "e")
            p(str(e), "e")

    def toTarget(self, results, tarSQL, dst, fnDic, numOfRows):
        targetObj = None
        try:
            targetObj = cnDb(dst[1], conType=dst[0])
            targetObj.cursor.executemany(tarSQL, results)
            targetObj.conn.commit()
            p('file->toTarget: FINISH Loading total of %s rows into target :%s ' % (str(numOfRows), str(dst[1])), "ii")
            targetObj.close()
        except Exception as e:
            p("file->toTarget: type: %s, name: %s ERROR in targetObj.cursor.executemany" % (self.cType, str(self.cName)),"e")
            p("file->toTarget: ERROR, target query: %s " % str(tarSQL), "e")
            p("file->toTarget: ERROR, sample result: %s " % str(results[0]), "e")
            p(str(e), "e")
            if targetObj and config.RESULT_LOOP_ON_ERROR :
                for r in results:
                    try:
                        r = [r]
                        targetObj.cursor.executemany(tarSQL, r)
                        targetObj.conn.commit()

                    except Exception as e:
                        ret = ""
                        for col in r[0]:
                            if col is None:
                                ret += str(col)+","
                            elif str(col).replace(".","").replace(",","").isdigit():
                                ret+=str(col)+" ,"
                            else :
                                ret += "'" + str(col) + "' ,"
                        p("file->toTarget: ERROR, LOOPING ON ALL RESULTS, ROW ERROR " , "e")
                        p(str(e), "e")
                        p(tarSQL, "e")
                        p(ret,"e")
                targetObj.close()
        return

    def dfToTable(self, df, ifExists='truncate', seq=None, index=False,chunksize=None):
        p("file->dfToTable: tranfering to file %s from data frame  >>>" % self.fullPath, "ii")

        if seq:
            p ("file->dfToTable: FILE %s, Sequence is not activated in target file connection, seq: %s  ..." %(str(self.fullPath) , str (seq) ), "e")

        if ifExists=='truncate':
            p("file->dfToTable: APPEND DATA  >>>" % self.fullPath, "ii")
            with open(self.cName, 'a') as f:
                df.to_csv(f , header=False, index=index, encoding=config.FILE_ENCODING, quoting=csv.QUOTE_NONNUMERIC,  quotechar = self.fileDelimiter)
        else:
            p("file->dfToTable: TRUNCATE AND LOAD DATA  >>>" % self.fullPath, "ii")
            df.to_csv(self.cName , header=False, index=index, encoding=config.FILE_ENCODING, quoting=csv.QUOTE_NONNUMERIC,  quotechar = self.fileDelimiter)

    def dfFromTable(self,srcColumns=None,tarColumn=None, index_col=None):
        p("file->dfFromTable: loading from file: %s into dataframe >>>" %self.fullPath, "ii")
        if self.fileHeader:
            df = pd.read_csv(filepath_or_buffer=self.fullPath, sep=self.fileDelimiter, encoding=config.FILE_DECODING, keep_default_na=False,
                             index_col=index_col, na_values=config.DATA_TYPE['null'][self.cType])  # , encoding="utf8" names=columns,

        else:
            df = pd.read_csv(filepath_or_buffer=self.fullPath, sep=self.fileDelimiter, encoding=config.FILE_DECODING, header=None, keep_default_na=False,
                             index_col=index_col, na_values=config.DATA_TYPE['null'][self.cType])  # , encoding="utf8" names=columns,

        if srcColumns:
            dfColumn = df.columns
            for i,col in enumerate (tarColumn):
                if srcColumns[i] in dfColumn:
                    df.rename(columns={srcColumns[i]: col}, inplace=True)
                else:
                    df.insert (i , col, '')

        return df.values.tolist()

    def __cloneObject(self, fullPath=None):
        fullPath = fullPath if fullPath else self.fullPath
        fileName = os.path.basename(fullPath)
        fileDir  = os.path.dirname(fullPath)
        fileNameNoExtenseion    = os.path.splitext(fileName)[0]
        fimeNameExtension       = os.path.splitext(fileName)[1]
        ### check if table exists - if exists, create new table
        isFileExists = os.path.isfile(fullPath)
        toUpdateFile = True


        if config.TABLE_HISTORY:
            p ("file-> __cloneObject: FILE History is ON ...", "ii")
            if isFileExists:
                actulSize = os.stat(fullPath).st_size
                if  actulSize<config.FILE_MIN_SIZE:
                    p("file-> __cloneObject: FILE %s exists, file size is %s which is less then %s bytes, will not update ..." % (fullPath, str(actulSize), str(config.FILE_MIN_SIZE)), "ii")
                    toUpdateFile = False
                else:
                    p("file-> __cloneObject: FILE %s exists, file size is %s which is bigger then %s bytes, file history will be kept ..." % (fullPath, str(actulSize), str(config.FILE_MIN_SIZE)), "ii")

            if toUpdateFile:
                oldName = None
                if (os.path.isfile(fullPath)):
                    oldName = fileNameNoExtenseion+"_"+str (time.strftime('%y%m%d'))+fimeNameExtension
                    oldName = os.path.join(fileDir, oldName)
                    if (os.path.isfile(oldName)):
                        num = 1
                        oldName= os.path.splitext(oldName)[0] + "_"+str (num) + os.path.splitext(oldName)[1]
                        oldName = os.path.join(fileDir, oldName)
                        while ( os.path.isfile(oldName) ):
                            num += 1
                            FileNoExt   = os.path.splitext(oldName)[0]
                            FileExt     = os.path.splitext(oldName)[1]
                            oldName=FileNoExt[: FileNoExt.rfind('_') ]+"_"+str (num) + FileExt
                            oldName = os.path.join(fileDir, oldName)
                if oldName:
                    p ("file-> __cloneObject: File History is ON, file %s exists ... will copy this file to %s " %(str (self.cName) , str(oldName) ), "ii")
                    shutil.copy(fullPath, oldName)
        else:
            if ( os.path.isfile(fullPath) ):
                os.remove(fullPath)
                p ("file-> __cloneObject: File History is OFF, and file %s exists, DELETE FILE >>>> " %(str (self.cName)  ), "ii")
            else:
                p ("file-> __cloneObject: File History is OFF, and file %s is not exists, continue >>>> " %(str (self.cName)  ), "ii")
