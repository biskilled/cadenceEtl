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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import re
import io
from collections            import OrderedDict

from popEtl.config          import config
from popEtl.glob.glob       import p, setDicConnValue, getDicKey
from popEtl.glob.enums      import eConnValues, ePopEtlProp
from popEtl.glob.globalDBFunctions import checkSequence, logsToDb
from popEtl.connections.connector  import connector

# mapping - change source data type to destination data type
def sourceToTargetDataTypes (srcType, trgType, srcColumns):
    if "file" in srcType.lower():
        srcType = trgType
    newColumns  = []
    mappDic     = {}
    ret         = None

    if "access" in srcType: srcType="sql"

    # source is same as target, data type ios the same
    if srcType == trgType:
        return srcColumns

    # loop on config.DATA_TYPE and create dictionary with source to target
    for dType in config.DATA_TYPE:
        srcTypes = None
        trgTypes = None
        if srcType in  config.DATA_TYPE[dType]: srcTypes = config.DATA_TYPE[dType][srcType]

        if trgType in config.DATA_TYPE[dType]: trgTypes = config.DATA_TYPE[dType][trgType]

        if srcTypes and trgTypes:
            if isinstance(srcTypes, tuple):
                for s in srcTypes:
                    if s not in mappDic:
                        mappDic[s] = trgTypes[0] if isinstance(trgTypes, tuple) else trgTypes
            else:
                if srcTypes not in mappDic:
                    mappDic[srcTypes] = trgTypes[0] if isinstance(trgTypes, tuple) else trgTypes

    if isinstance( srcColumns, (dict, OrderedDict) ):
        listTarToSrc = [(x,srcColumns[x]["t"]) for x in srcColumns if "t" in srcColumns[x]]
    else:
        listTarToSrc = srcColumns

    # update pre/post column
    # update column with targer data type
    for col in listTarToSrc:
        columnName      = col[0]
        columnType      = col[1].replace(' ','')
        replaceString   = ""
        postType        = None
        # metch string(...) pattern


        fmatch = re.search (r'(.*)(\(.+\))',columnType, re.M|re.I)
        newField = config.DATA_TYPE['default'][trgType]
        if fmatch:
            replaceString   = fmatch.group(1)   # --> varchar, int , ...
            postType        = fmatch.group(2)   # --> (X), (X,X) , ....
        else:
            replaceString = columnType

        if replaceString in mappDic:
            newField = mappDic[replaceString]
            if postType:
                # for my sql only !! - int(11) will be considered as int ...
                newField +=postType if 'int' not in replaceString else ""
        newColumns.append ( (columnName , newField) )

    if isinstance( srcColumns, (dict, OrderedDict) ):
        for tup in newColumns:
            existsVal = srcColumns[tup[0]]
            existsVal["t"] = tup[1]
            srcColumns[tup[0]] = existsVal
        ret = srcColumns
    else:
        ret = newColumns

    p ("mapper->sourceToTargetDataTypes: source data types converted to destination. new dataTpe: %s >>>>" %(str(newColumns)) ,"ii")
    return ret

# dictionary with keys : 'source','target','columns','mapping'
def mapper (dicProp):
    prop        = dicProp.keys()
    toCreate    = []

    #update parmaters
    isMerge         = dicProp[ePopEtlProp.mrg] if ePopEtlProp.mrg in prop else None
    stt             = dicProp[ePopEtlProp.stt] if ePopEtlProp.stt in prop else None
    seq             = checkSequence (dicProp[ePopEtlProp.seq]) if ePopEtlProp.seq in prop else None
    isTarget        = dicProp[ePopEtlProp.tar] if ePopEtlProp.tar in prop else None
    isSource        = dicProp[ePopEtlProp.src] if ePopEtlProp.src in prop else None
    addSourceColumn = dicProp[ePopEtlProp.add] if ePopEtlProp.add in prop else False

    # There is Target mapping
    if not isTarget:
        p("mapper->mapper: Target is not exists, What the hell quittttitnnggggg.... >>>>>>>>>>", "i")
        return

    # There is direct source
    if isSource:
        stt         = isSource.structure(stt=stt,addSourceColumn=addSourceColumn)
        srcColumns  = isSource.getColumns()

        # convert source data type to target data types
        srcColumns      = sourceToTargetDataTypes(isSource.cType, isTarget.cType, srcColumns)
        srcColumnNames  = [c[0].strip() for c in srcColumns]

        updColumns      = []
        if srcColumns and len (srcColumns)>0:
            # there is target, source and mapping Will map field based on source and create table
            if stt and len(stt)>0:
                srcC = [stt[k]["s"] for k in stt if "s" in stt[k]]

                # check if all mapping exist in source as well
                for col in srcC:
                    if col not in srcColumnNames:
                        colTodel = [k for k in stt if "s" in stt[k] and stt[k]["s"]==col]
                        p ('mapper->mapper: There is Targets %s which is mapped to %s, but source not exists, ignoring targets column %s ....' %(str(colTodel), col,str(colTodel) ) ,"ii")
                        p('mapper->mapper: SOURCE COLUMNS : '  , "ii")
                        srcNameStr = ""
                        for s in srcColumnNames:
                            srcNameStr+=s+" ,"
                        p(srcNameStr, "ii")
                        for d in colTodel:
                            del stt[d]

                # Update stt with new types
                stt = sourceToTargetDataTypes(isSource.cType, isTarget.cType, stt)

            isTarget.create(stt=stt, seq=seq)
            if isMerge: isMerge.create(stt=stt, seq=seq)
        else:
            p ("mapper->mapper: Source %s is not exists, will not create target table >>>>>>>>>>" %str(isSource.cName),"e")
    # there is only target
    elif stt:
        for t in stt:
            if "t" not in stt[t]:
                p('mapper->mapper: There is Target mapping without Source, there is NO TYPE for column %s, ignoring column, values is %s ....' % (str(t), str(stt[t])), "ii")
                del stt[t]
            if "s" not in stt[t]:
                stt[t]["s"]=t
        isTarget.create(stt=stt, seq=seq)
    elif isMerge:
        stt = isTarget.structure(stt=stt, addSourceColumn=addSourceColumn)
        isMerge.create (stt=stt,seq=seq)

def _extractNodes (jText,jFileName,sourceList=None, destList=None):
    sttDic = OrderedDict()
    for jMap in jText:
        toLoad = True
        dicProp = {}
        srcObj  = None
        tarObj  = None
        sttDic  = OrderedDict()
        dicProp[ ePopEtlProp.add ] = False

        if isinstance(jMap, (list,tuple)):
            _extractNodes(jText=jMap, jFileName=jFileName, sourceList=sourceList, destList=destList)
            continue

        keys = [x.lower() for x in jMap.keys()]
        # update all variables
        sourceConn      = getDicKey(ePopEtlProp.src,keys)
        queryConn       = getDicKey(ePopEtlProp.qry,keys)
        targetConn      = getDicKey(ePopEtlProp.tar,keys)
        mergeConn       = getDicKey(ePopEtlProp.mrg,keys)
        seqFiles        = getDicKey(ePopEtlProp.seq,keys)
        stt             = getDicKey(ePopEtlProp.stt,keys)
        targetMapping   = getDicKey(ePopEtlProp.map,keys)
        targetColumn    = getDicKey(ePopEtlProp.col,keys)

        if sourceConn:
            connDic = setDicConnValue (connJsonVal=jMap[sourceConn],extraConnVal=jFileName, isSource=True )
            srcObj  = connDic [ eConnValues.connObj ] if connDic else None
            dicProp[ePopEtlProp.src] = connector(connDic = connDic)

        if queryConn:
            connDic = setDicConnValue(connJsonVal=jMap[queryConn], extraConnVal=jFileName, isSource=True, isSql=True)
            dicProp[ePopEtlProp.src] = connector(connDic = connDic)
            if sourceConn:
                p("mappr->_extractNodes: There is query and source, will be QUERY sed as SOURCE object >>>>>> ", "ii")

        # target -> Connection object
        if targetConn:
            connDic = setDicConnValue(connJsonVal=jMap[targetConn], connObj=tarObj, extraConnVal=jFileName,  isTarget=True)
            tarObj = connDic[eConnValues.connObj] if connDic else None
            dicProp[ePopEtlProp.tar] = connector(connDic = connDic)

        # create table with sequence as fisrt column -> apply on target only ! (if there is merge - will use merge option, without adding identity
        if seqFiles:
            # check sequence dictionay
            dicProp[ePopEtlProp.seq] = checkSequence(jMap[seqFiles])
            # add property - if merge is appear
            if mergeConn and ePopEtlProp.seq in dicProp and len(dicProp[ePopEtlProp.seq]) > 0:
                dicProp[ePopEtlProp.seq][ePopEtlProp.mrg] = True

        # Check stt (source to target) --> if needs to add columns or new mapping
        if stt:
            sttDic = jMap[stt]
            dicProp[ePopEtlProp.stt] = sttDic
            if ePopEtlProp.sttA in stt:  dicProp[ePopEtlProp.add] = True

        # Mapping source to target fields
        if targetMapping:
            dicProp[ePopEtlProp.add] = False
            if targetConn and (sourceConn or queryConn) :
                mapping = jMap[targetMapping]
                sttDicTemp = sttDic
                sttDic = OrderedDict()
                for m in mapping:
                    if m in sttDicTemp:
                        sttDic[m] = sttDicTemp[m]
                        if "s" not in sttDic[m]:
                            sttDic[m]["s"] = mapping[m]
                    else:
                        sttDic[m] = {"s": mapping[m]}
                for t in sttDicTemp:
                    if t not in sttDic: sttDic[t] = sttDicTemp[t]
                dicProp[ePopEtlProp.stt] = sttDic
            else:
                p("mappr->loadJson: Mapping exists, but there is no target or source connection ... nothing to do ...","e")

        # Create target column by column definitions
        if targetColumn:
            if targetConn:
                columns = jMap[targetColumn]
                sttDicTemp = sttDic
                sttDic = OrderedDict()
                for c in columns:
                    if c in sttDicTemp:
                        sttDic[c] = sttDicTemp[c]
                        if "t" not in sttDic[c]:
                            sttDic[c]["t"] = columns[c]
                    else:
                        sttDic[c] = {"t": columns[c]}
                for t in sttDicTemp:
                    if t not in sttDic: sttDic[t] = sttDicTemp[t]
                dicProp[ePopEtlProp.stt] = sttDic
                dicProp[ePopEtlProp.tar].setColumns(sttDic)
            else:
                p("mappr->loadJson: Target columns exists, but there is no target connection ... nothing to do ...","e")

        # checl list of source or target to load (if list exists)
        if sourceList:
            sourceList = [x.lower() for x in sourceList]
            toLoad = True if ePopEtlProp.src in dicProp and dicProp[ePopEtlProp.src].cName in sourceList else False
        if destList:
            destList = [x.lower() for x in destList]
            toLoad = True if ePopEtlProp.tar in dicProp and dicProp[ePopEtlProp.tar].cName in destList else False

        if toLoad:
            mapper(dicProp=dicProp)
        else:
            p("mappr->loadJson: Src %s, dst %s , mapping %s not matched >>>> nothing to map " % (
            str(sourceList), str(destList), str(dicProp)), "i")

# Main function : loading all json file and parse them by definition
def model (dicObj=None, sourceList=None, destList=None):
    p('mapper->model: START MAPPING >>>>>', "i")

    if dicObj:
        dicObj = list (dicObj) if isinstance(dicObj, (dict,OrderedDict)) else dicObj
        p('mapper->model: loading from Dictionary  >>>>>' , "ii")
        _extractNodes(jText=dicObj, jFileName='', sourceList=sourceList, destList=destList)
    else:
        jsonFiles = [pos_json for pos_json in os.listdir(config.DIR_DATA) if pos_json.endswith('.json')]
        for f in list (jsonFiles):
            if f in config.FILES_NOT_INCLUDE:   jsonFiles.remove(f)

        for index, js in enumerate(jsonFiles):
            with io.open(os.path.join(config.DIR_DATA, js), encoding='utf-8') as jsonFile:
                p('mapper->model: start modeling from file  %s, folder: %s >>>>>' % (js, str(config.DIR_DATA)), "ii")
                jText = json.load(jsonFile , object_pairs_hook=OrderedDict)
                _extractNodes(jText=jText, jFileName=js, sourceList=sourceList, destList=destList)

    if config.LOGS_IN_DB: logsToDb()
    p ('mapper->model: FINISH MAPPING >>>>>', "i")
    p ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', "ii")