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
import codecs
import pandas as pd
from collections import OrderedDict

from popEtl.config          import config
from popEtl.glob.glob       import p
from popEtl.glob.enums      import eConnValues, eDbType


class cnFile ():
    def __init__ (self, connDic, connName=None, connFolder=None, fileHeader=[]):
        self.cName      = connDic [ eConnValues.connObj ]  if connDic else connName
        self.cType      = connDic [ eConnValues.connType ] if connDic else eDbType.FILE
        self.folderPath = connDic [ eConnValues.connUrl ]  if connDic else connFolder
        self.fileHeader = fileHeader
        self.cursor     = None
        self.conn       = None
        self.cColumns   = None

        if isinstance(self.folderPath, (dict, OrderedDict)):
            connProp = self.folderPath.keys()
        self.fileDelimiter  = self.folderPath['delimiter']  if 'delimiter'   in connProp    else config.FILE_DEFAULT_DELIMITER
        self.fileHeader     = self.folderPath['header']     if 'header' in connProp         else config.FILE_DEFAULT_HEADER
        self.folderPath     = self.folderPath['folder']     if 'folder' in connProp         else config.FILE_DEFAULT_FOLDER
        self.fullPath       = os.path.join(self.folderPath, self.cName)
        self.newLine        = self.folderPath['newLine']    if 'newLine' in connProp        else config.FILE_DEFAULT_NEWLINE
        self.encoding       = self.folderPath['encoding']   if 'encoding' in connProp       else config.FILE_DECODING
        self.errors         = self.folderPath['errors']     if 'errors' in connProp         else config.FILE_LOAD_WITH_CHAR_ERR

        head, tail = os.path.split (self.cName)
        if head and len(head)>1 and tail and len (tail)>1:
            self.fullPath = self.cName
        else:
            self.fullPath = os.path.join(self.folderPath, self.cName)
        p ("file-> INIT: %s, Delimiter %s, Header %s " %(str(self.fullPath) , str(self.fileDelimiter) ,str(self.fileHeader) ), "ii")

    def close (self):
        pass

    def truncate(self, tbl=None):
        if os.path.isfile(self.fullPath):
            os.remove(self.fullPath)
            p("file->truncate: %s is deleted " %(self.fullPath))
        else:
            p("file->truncate: %s is not exists " % (self.fullPath))

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

    def loadData(self, srcVsTar, results, numOfRows, cntColumn):
        headerList = None
        if self.fileHeader:
            if srcVsTar:
                headerList = [t[1] for t in srcVsTar]
            else:
                headerList = ["col%s" %i for i in range ( cntColumn ) ]

        with codecs.open( filename=self.fullPath, mode='wb', encoding="utf8") as f:
            if headerList:
                f.write (u",".join(headerList))
                f.write("\n")

            for row in results:
                row = [unicode(s)  for s in row]
                f.write(u",".join(row))
                f.write("\n")

        p('file->loadData: Load %s into target: %s >>>>>> ' % (str(numOfRows), self.fullPath), "ii")
        return

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
