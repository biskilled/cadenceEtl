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
import sys
import shutil
import time
import io
import traceback
import codecs
from collections import OrderedDict

from popEtl.config          import config
from popEtl.glob.glob       import p, decodeStrPython2Or3, functionResultMapping
from popEtl.glob.enums      import eConnValues, eDbType


class cnFile ():
    def __init__ (self, connDic=None, connType=None, connName=None, connUrl=None, connObj=None, fileHeader=[]):
        self.cType= connDic[eConnValues.connType] if connDic else connType if connType else eDbType.FILE
        self.cName= connDic[eConnValues.connObj]  if connDic else connName if connName else self.cType
        self.cUrl = connDic[eConnValues.connUrl]  if connDic else connUrl
        self.cObj = connDic[eConnValues.connObj]  if connDic else connObj if connObj else None
        self.cursor     = None
        self.conn       = None
        self.cColumns   = None
        self.cFilter    = None
        self.fileHeader = fileHeader

        fileDicDef = self.cUrl if isinstance(self.cUrl, (dict, OrderedDict)) else {}
        connProp = [x.lower() for x in self.cUrl.keys()]

        self.fileDelimiter  = self.cUrl[eConnValues.fileDelimiter] if eConnValues.fileDelimiter in connProp else config.FILE_DEFAULT_DELIMITER
        self.fileHeader     = self.cUrl[eConnValues.fileHeader] if eConnValues.fileHeader in connProp       else config.FILE_DEFAULT_HEADER
        self.folderPath     = self.cUrl[eConnValues.fileFolder] if eConnValues.fileFolder in connProp       else config.FILE_DEFAULT_FOLDER
        self.fullPath       = os.path.join(self.folderPath, self.cObj) if self.cObj else None
        self.newLine        = self.folderPath[eConnValues.fileNewLine]  if eConnValues.fileNewLine in connProp  else config.FILE_DEFAULT_NEWLINE
        self.encoding       = self.folderPath[eConnValues.fileEncoding] if eConnValues.fileEncoding in connProp else config.FILE_DECODING
        self.errors         = self.folderPath[eConnValues.fileErrors]   if eConnValues.fileErrors in connProp   else config.FILE_LOAD_WITH_CHAR_ERR

        if self.cObj:
            head, tail = os.path.split (self.cObj)
            if head and len(head)>1 and tail and len (tail)>1:
                self.fullPath = self.cObj
            else:
                self.fullPath = os.path.join(self.folderPath, self.cObj)
            if (os.path.isfile(self.fullPath)):
                p ("file-> INIT: %s, Delimiter %s, Header %s " %(str(self.fullPath) , str(self.fileDelimiter) ,str(self.fileHeader) ), "ii")

    def connect( self, fileName=None):
        if fileName:
            self.fullPath = fileName
            return True
        elif not self.fullPath:
            if self.folderPath and os.path.isdir(self.folderPath):
                p("Connected to folder %s" %self.folderPath)
                return True
            else:
                err = u"File path is valid: %s " %(decodeStrPython2Or3(self.fullPath))
                raise ValueError(err)

    def close (self):
        pass

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

    def truncate(self, tbl=None):
        if os.path.isfile(self.fullPath):
            os.remove(self.fullPath)
            p("file->truncate: %s is deleted " %(self.fullPath))
        else:
            p("file->truncate: %s is not exists " % (self.fullPath))

    def getColumnsTypes (self):
        if self.cColumns and len(self.cColumns)>0:
            return self.cColumns
        else:
            self.structure (stt=None)
        return self.cColumns

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

    def transferToTarget(self, dstObj, srcVsTar, fnDic, pp):
        results     = []
        header      = []
        cntColumn   = 0

        srcNames = [st[0] for st in srcVsTar] if srcVsTar else []
        tarNames = [st[1] for st in srcVsTar] if srcVsTar else []
        srcVsTar = list ([])

        try:
            with io.open (self.fullPath, 'r', encoding='windows-1255', errors=self.errors) as fFile: # encoding='windows-1255' encoding='utf8'
                for i, line in enumerate(fFile):
                    line = line.replace('"', '').replace("\t", "")
                    line = line.strip(config.FILE_DEFAULT_NEWLINE)
                    split_line = line.split(self.fileDelimiter)
                    # Add headers structure
                    if i==0:
                        split_line = [c.strip() for c in split_line]
                        if self.fileHeader and len (srcNames)>0:
                            for i, sCol in enumerate (srcNames):
                                if sCol in split_line:
                                    header.append (split_line.index(sCol))
                                    srcVsTar.append ((sCol,tarNames[i],))
                                elif sCol == "''":
                                    header.append(sCol)
                                    srcVsTar.append((sCol, tarNames[i],))
                                else:
                                    p ("file->transferToTarget: Loading %s, column %s mapped but not found in file headers, ignoring %s ..." %(str(self.fullPath), str(sCol), str(split_line)))
                            continue
                        else:
                            for i, sCol in enumerate(split_line):
                                colName = '%s%s' %(str(config.FILE_DEF_COLUMN_PREF),str(i))
                                header.append(i)
                                srcVsTar.append ( (i, colName ))

                        cntColumn = len (header)


                    results.append(split_line)
                    if config.FILE_MAX_LINES_PARSE>0 and i>0 and i%config.FILE_MAX_LINES_PARSE == 0:
                        results = functionResultMapping( results, fnDic, header=header)
                        dstObj.loadData(srcVsTar, results, i, cntColumn)
                        results = list ([])

                if len(results)>0 : #and split_line:
                    results = functionResultMapping(results, fnDic, header=header)
                    dstObj.loadData(srcVsTar, results, len(results), len(srcVsTar))
                    #self.__checkColumn (srcVsTar, results, dstObj, maxRows=None,numOfCol=47)
                    results = list ([])

        except Exception as e:
            p("file->transferToTarget: ERROR loading file: %s, type: %s >>>>>>" % (self.cName, self.cType) , "e")
            p(traceback.format_exc(),"e")


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

    def __checkColumn (self, srcVsTar, results, dstObj, maxRows=None, numOfCol=None):
        rrRan = [numOfCol] if numOfCol else range(1, len (srcVsTar))

        if results and len(results)>0:
            totalCol = len (results[0])
            for cntCol in rrRan:
                if cntCol<=totalCol:
                    dstObj.truncate()
                    nres = []
                    nCol = srcVsTar[:cntCol]
                    for i, rr in enumerate (results):
                        if maxRows and i>maxRows:
                            break
                        nres.append( rr[:cntCol] )

                    p ("__checkColumn:check %s out of %s columns" %(str(cntCol), str(totalCol)))
                    dstObj.loadData(nCol, nres, len(nres), cntCol)