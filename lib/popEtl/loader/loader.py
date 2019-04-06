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

import os
import json
import multiprocessing
import time
import io
from collections import OrderedDict, Counter

from popEtl.config                  import config
from popEtl.glob.glob               import p, setQueryWithParams, getDicKey, filterFiles
from popEtl.glob.enums              import eConnValues, ePopEtlProp
from popEtl.connections.dbSqlLite   import sqlLite
from popEtl.connections.connector   import connector
from popEtl.glob.globalDBFunctions  import logsToDb

# Will merge table with connection in source object
def _execMerge (dstObj, mergeConn, sttDic, toCreate=True):

    mergeKeys = None
    if isinstance( mergeConn , (list,tuple) ):
        mergeTable = mergeConn[0]
        mergeKeys  = mergeConn[1]
        if len (mergeConn) == 3:
            toCreate = mergeConn[2]
    else:
        mergeTable = mergeConn

    dstObj.connect()
    # create target table same as source one
    if toCreate:
        dstObj.create (stt=sttDic, tblName=mergeTable )

    dstObj.merge (mergeTable=mergeTable, mergeKeys=mergeKeys)
    dstObj.close()

def _appendPartitions (srcObj, partition):
    srcName = srcObj.cObj
    ret = []
    sqlStart = "SELECT * FROM %s WHERE " %(srcName)
    if eConnValues.partitionCol in partition:
        colToFilter = partition[ eConnValues.partitionCol ]
    else:
        p("loader->_appendPartitions: There is partition without column definition table: %s ..." % (srcName), "e")
        return ret

    if eConnValues.partitionAgg in partition:
        resolution = partition[ eConnValues.partitionAgg ]
        srcObj.connect()

        # Set starting from partition
        if eConnValues.partitionStart in partition:
            minDate = srcObj.minValues (resolution=resolution, periods=partition[ eConnValues.partitionStart ])
        else:
            minDate = srcObj.minValues (colToFilter=colToFilter, resolution=resolution)

        lastDate = srcObj.minValues (resolution=resolution, periods=0)

        while minDate<lastDate:
            newDate = srcObj.minValues (resolution=resolution, periods=1, startDate=minDate)
            if newDate < lastDate:
                sqlWhere = sqlStart+"%s >= '%s' and %s < '%s'" %(colToFilter,minDate,colToFilter,newDate)
            else:
                sqlWhere = sqlStart + "%s >= '%s'" % (colToFilter, minDate)
            minDate = newDate
            ret.append(sqlWhere)
        srcObj.close()
    else:
        p ("loader->_appendPartitions: There is partition without aggragation function, needs to have 'agg' with values of 'd', 'm' or 'y', table: %s ..." %(str (src)) , "e")
    return ret

# jMap, src, dst
def _execTarget (dstObj):
    if dstObj.cFilter:
        dstObj.connect()
        sql = "Delete From " + dstObj.cName + " Where " + dstObj.cFilter
        sql = setQueryWithParams(sql)
        p("loader->_execTarget: Destination %s have delete query %s, deleting target " % (dstObj.cName, sql), "ii")
        dstObj.execSP(sqlQuery=sql)
        dstObj.close()

    if config.TO_TRUNCATE:
        dstObj.connect()
        p("loader->_execTarget: Destination %s is trancating  " % (dstObj.cName), "ii")
        dstObj.truncate()
        dstObj.close()
    return

def _execSql (execObj):
    execObj.connect()
    execObj.execSP()
    execObj.close()
    p("loader->_execSql: exec  %s " % (execObj.cName), "i")
    return

def _updateSourceTargetCompareLog (js):
    isRepoTblsExists  = False
    connUrl     = None
    connType    = None

    with open(os.path.join(config.DIR_DATA, js)) as jsonFile:
        jText = json.load(jsonFile, object_pairs_hook=OrderedDict)

    p("loader->_updateSourceTargetCompareLog: Loading from file %s COMPARE number of rows in Source vs target " % (str(js)),"i")
    for connType in config.CONN_URL:
        if "repo" in connType.lower():
            connUrl     = config.CONN_URL[connType]
            connType    = connType.lower()
            connType    = connType.replace("repo","")
            isRepoTblsExists = True
            break

    if isRepoTblsExists:
        for jMap in jText:
            keys        = map(lambda x: x.lower(), jMap.keys())
            dst         = {'target', 'tar'}.intersection(set(keys))
            src         = {'source','src'}.intersection(set(keys))
            query       = {'query'}.intersection(set(keys))

            # exists source/query AND destination OR destination and merge only
            if len(dst)>0 and (len(src)>0 or len(query)>0)  :
                query   = query.pop()           if len (query)>0    else None
                isSql   = True                  if query            else False

                # will use dst if exists. if not-> will use source if exists, if not will use query                                 dst->src->query
                dst     = dst.pop() if len(dst)>0 else src.pop() if len(src)>0 else query
                src     = src.pop() if len(src)>0 else query if query else dst
                src = jMap[src]
                dst = jMap[dst]



                if "access" in src[0]:
                    accessFilePath = config.CONN_URL["access"][0] % (
                    config.CONN_URL["access"][1] + str(js.split(".")[0] + ".accdb"))
                    srcObj = connector(connProp=src, connUrl=accessFilePath, isSql=isSql)
                else:
                    srcObj = connector(connProp=src, isSql=isSql)

                dstObj = connector( dst )
                tblDstName = dst[1]
                tblDstType = dst[0]
                tblSrcName = src[1]
                tblSrcType = src[0]
                cntSrc = srcObj.cntRows()
                cntTar = dstObj.cntRows()
                srcObj.close()
                dstObj.close()

                localTime = time.localtime()
                timeStr = time.strftime("%m/%d/%Y %H:%M:%S", localTime)

                logObj = connector ([connType,"logs"], connUrl=connUrl)
                sql = "Insert into "+config.LOGS_COUNT_SRC_DST+" select "
                sql+="'" + timeStr + "'"
                sql += "'" + tblDstName + "',"
                sql += "'" + tblDstType + "',"
                sql +=  str(cntTar)  + ","
                sql += "'" + tblSrcName + "',"
                sql += "'" + tblSrcType + "',"
                sql += str(cntSrc) + ""

                logObj.cursor.execute (sql)
                logObj.conn.commit()
                logObj.close()

# jMap, src, dst, sttDic, isSQL, merge, inc, seq
def _execLoading ( params ):
    (srcObj, dstObj, mergeConn, sttDic, jFileName, cProc, tProc) = params
    if srcObj and dstObj:
        p("loader->_execLoading: loading %s out of %s, src: %s, dst: %s " %(str(cProc), str(tProc), str(srcDict[eConnValues.connName]), str(dstDict[eConnValues.connName])), "i")

        # Managing Destination table
        _execTarget(dstObj=dstObj)

        # True / False indication
        addSourceColumn = False
        if sttDic and config.STT_INTERNAL in sttDic:
            addSourceColumn = sttDic[config.STT_INTERNAL]
            del sttDic[config.STT_INTERNAL]

        srcObj.connect()
        dstObj.connect()

        # Check if source is same as target connection (only for merge option)
        if srcObj.cType==srcObj.cType  and srcObj.cObj ==  dstObj.cObj:
            p('loader->execLoading: TYPE: %s, SOURCE and TARGET %s object are identical.. will check if there is merge >>>>>' % (str(srcDict[eConnValues.connType]), str(srcDict[eConnValues.connObj])), "ii")

        else:
            sttDic = srcObj.structure(stt=sttDic, addSourceColumn=addSourceColumn)
            # isSQL, columnInc, columnStart = addIncemenral (inc, isSQL, srcObj, srcMapping)
            srcObj.transferToTarget(dstObj=dstObj, sttDic=sttDic)
            srcObj.close()
            dstObj.close()

    if mergeConn:
        p("loader->_execLoading: MERGE !!!! " , "i")
        if not dstObj:
            dstDict = srcObj
        _execMerge(dstObj=dstObj, mergeConn=mergeConn, sttDic=None, toCreate=True)
        return

    if config.LOGS_IN_DB : logsToDb( str(jFileName)+":"+str(dstObj.cName) )

def _extractNodes (jText,jFileName,sourceList=None, destList=None, singleProcess=None):
    processList = []
    loadedObject= []
    cProc       = 0
    for jMap in jText:
        # if there is a list - will exec nodes in on a single process
        if isinstance(jMap, (list,tuple)):
            loadedObject = _extractNodes(jText=jMap, jFileName=jFileName,
                                         sourceList=sourceList, destList=destList,
                                         singleProcess=True)
            continue

        srcObj = None
        tarObj = None
        execObj= None
        toLoad = True

        keys = [x.lower() for x in jMap.keys()]
        sourceConn      = getDicKey(ePopEtlProp.src, keys)
        queryConn       = getDicKey(ePopEtlProp.qry, keys)
        targetConn      = getDicKey(ePopEtlProp.tar, keys)
        mergeConn       = getDicKey(ePopEtlProp.mrg, keys)
        seq             = getDicKey(ePopEtlProp.seq, keys)
        stt             = getDicKey(ePopEtlProp.stt, keys)
        targetMapping   = getDicKey(ePopEtlProp.map, keys)

        partition       = getDicKey(ePopEtlProp.par,keys)
        inc             = getDicKey(ePopEtlProp.inc,keys)
        execSql         = getDicKey(ePopEtlProp.exe,keys)


        sttDic          = jMap[stt]  if stt and len (jMap[stt])>0 else None
        mergeConn       = jMap[mergeConn]  if mergeConn and len (jMap[mergeConn])>0 else None

        if queryConn:
            p("loader->_extractNodes: Found %s and %s, will use %s as source data " % (ePopEtlProp.src, ePopEtlProp.qry, ePopEtlProp.qry), "i")
            srcObj = connector(connJsonVal=jMap[queryConn], extraConnVal=jFileName, isSource=True, isSql=True)
        if sourceConn:
            if srcObj is not None:
                p("loader->_extractNodes: Found %s and %s, will use %s as source data " % (ePopEtlProp.src, ePopEtlProp.qry, ePopEtlProp.qry), "i")
            else:
                srcObj = connector(connJsonVal=jMap[sourceConn], extraConnVal=jFileName, isSource=True)

        tarObj = connector(connJsonVal=jMap[targetConn], extraConnVal=jFileName, isTarget=True) if targetConn else None
        execObj= connector(connJsonVal=jMap[execSql], extraConnVal=jFileName, isSql=True) if execSql else None

        # if exec Sql is first
        if execObj:
            locSql = keys.index(execSql)
            if locSql==0: _execSql(execObj)
            if len(keys) == 1:
                continue


        # if there is source and target or merge with source/target
        if (srcObj and tarObj) or (mergeConn and (srcObj or tarObj)):
            # update sttDic with mapping -> if exists
            if tarObj:
                if sttDic:
                    sttDicTemp = sttDic
                    sttDic = OrderedDict()
                    if targetMapping:
                        for t in targetMapping:
                            if t in sttDicTemp:
                                sttDic[t] = sttDicTemp[t]
                                if "s" not in sttDic[t]:
                                    sttDic[t]["s"] = targetMapping[t]
                            else:
                                sttDic[t] = {"s": targetMapping[t]}
                    if sttDicTemp:
                        for t in sttDicTemp:
                            if t not in sttDic: sttDic[t] = sttDicTemp[t]
                elif targetMapping:
                    sttDic = OrderedDict()
                    for t in targetMapping:
                        sttDic[t] = {"s": targetMapping[t]}

            sttDic = sttDic if sttDic and len(sttDic) > 0 else None
            # Update sttDic
            if sttDic:
                sttDic[config.STT_INTERNAL] = True if ePopEtlProp.sttA == stt.lower() and not targetMapping else False

            if sourceList:
                sourceList = [x.lower() for x in sourceList]
                toLoad = True if srcObj.cName in sourceList or srcObj.cObj in sourceList else False
            if destList:
                destList = [x.lower() for x in destList]
                toLoad = True if tarObj.cName in destList or tarObj.connObj in destList else False

            if toLoad:
                if srcObj and tarObj:
                    p('loader->_extractNodes: SOURCE %s -> TARET %s ; %s -->  %s .......' % (str(srcObj[ eConnValues.connType ]), str(tarObj[ eConnValues.connType ]), srcDic[ eConnValues.connName ], tarDic[ eConnValues.connName ]), "ii")
                if tarObj and mergeConn:
                    p('loader->_extractNodes: Type: %s, TAREGT -> MERGE %s  .......' % (str(tarObj[eConnValues.connType]), tarObj[eConnValues.connName]), "ii")
                if srcObj and mergeConn:
                    p('loader->_extractNodes: Type: %s, SOURCE -> MERGE %s  .......' % (str(srcObj[eConnValues.connType]), srcObj[eConnValues.connName]), "ii")
                # if partition --> change to all partitions
                # update list of data to process:
                if partition:
                    if inc:
                        p('loader->_extractNodes: Cannot have incremental and partiton loading methods.. will use partiton method >>>>>',"ii")
                    if not queryConn or len(queryConn) < 1:
                        newSqlList = _appendPartitions(srcObj, partition)
                        for newSql in newSqlList:
                            cProc += 1
                            tmpParObj = connector (connJsonVal=None,
                                                         connType= srcObj.cType,
                                                         connName= srcObj.cName,
                                                         connObj=newSql,
                                                         connFilter=None,
                                                         connUrl=None, extraConnVal=None, isSql=True,
                                                         isTarget=False, isSource=True)
                            if singleProcess:
                                _execLoading((tmpParObj, tarObj, mergeConn, sttDic, jFileName, cProc, 1))
                            else:
                                processList.append((tmpParObj, tarObj, mergeConn, sttDic, jFileName, cProc))

                        loadedObject.append("P: %s; " %tarObj.cObj )
                    else:
                        cProc += 1
                        p('loader->_extractNodes: Cannot have partition with query as source.. will use query as is, sql: %s >>>>>' % (str(srcDic [ eConnValues.connObj ])), "ii")
                        if singleProcess:
                            _execLoading( (srcObj, tarObj, mergeConn, sttDic, jFileName, cProc, 1) )
                        else:
                            processList.append((srcObj, tarObj, mergeConn, sttDic, jFileName, cProc))
                else:
                    cProc += 1
                    if singleProcess:
                        _execLoading((srcObj, tarObj, mergeConn, sttDic, jFileName, cProc , 1))
                    else:
                        processList.append((srcObj, tarObj, mergeConn, sttDic, jFileName, cProc))
                if tarObj:
                    loadedObject.append("%s; " %( tarObj.cObj ))
                if mergeConn:
                    mergTbl = mergeConn[0] if isinstance(mergeConn, (list,tuple)) else mergeConn
                    loadedObject.append("MERGE: %s; " % (mergTbl))
        else:
            p("loader->_extractNodes: There is nothing to do >>>>>>>>>>>>>>", "i")

        # Strat runing all processes per file

    numOfProcesses = len(processList) if len(processList) < config.NUM_OF_PROCESSES else config.NUM_OF_PROCESSES

    # Add total processes to execute
    for i, itemP in enumerate(processList):
        processList[i] = itemP + (cProc,)


    if numOfProcesses > 1:
        proc = multiprocessing.Pool(config.NUM_OF_PROCESSES).map(_execLoading, processList)
    elif numOfProcesses > 0:
            for etl in processList:
                _execLoading(etl)

    return loadedObject

def trasnfer (dicObj=None, sourceList=None, destList=None):
    loadedObject = []
    if dicObj:
        dicObj = list (dicObj) if isinstance(dicObj, (dict,OrderedDict)) else dicObj
        p('loader->loading: loading from Dictionary >>>>>' , "ii")
        loadedObject = _extractNodes(jText=dicObj, jFileName='', sourceList=sourceList, destList=destList)
    else:
        jsonFiles = filterFiles(modelToExec="loader->loading", dirData=None, includeFiles=None, notIncludeFiles=None)

        for index, js in enumerate(jsonFiles):
            with io.open(os.path.join(config.DIR_DATA, js), encoding="utf-8") as jsonFile:           #
                jText = json.load(jsonFile, object_pairs_hook=OrderedDict)

            p("loader->loading: Start loading from file %s, folder: %s >>>>> >>>>>>" %(str(js), str(config.DIR_DATA)), "i")
            loadedObject = _extractNodes(jText, jFileName=js, sourceList=sourceList, destList=destList)
            p("loader->loading: Finish loading from file %s >>>>>>" %(str(js)), "i")
            if config.LOGS_COUNT_SRC_DST: _updateSourceTargetCompareLog(js)

    if config.LOGS_IN_DB: logsToDb()
    p("loader->loading: FINISH LOADING, Loader into : " + str (loadedObject), "i")

if __name__ == '__main__':
    multiprocessing.freeze_support()



##############   Not in used - need to check            #####################################
# Saving into file new sequence
def addIncSaveToFile (df, columnInc, srcObj):
    if df is not None and columnInc in df.columns:
        maxValue = df[columnInc].max()
        if str(maxValue).lower() == 'nan':
            p("loader->addSeqSaveToFile: df is empty - there are no rows to add into column %s " % (str(columnInc)), "ii")
            return
        else:
            db = sqlLite(os.path.join(config.DIR_DATA, config.SEQ_DB_FILE_NAME))
            db.execReplaceSql(srcObj.objName, columnInc, maxValue)
            db.close()
    else:
        p ("loader->addSeqSaveToFile: df is not exists or column %s is not in dataframe" %(str(columnInc)) , "ii")

def addIncemenral (inc, isSQL, srcObj, srcMapping=None):
    if not inc:
        return isSQL, None, None

    columnSeq = inc['column']
    columnStart = inc['start'] if 'start' in inc else 0
    db = sqlLite ( os.path.join(config.DIR_DATA, config.SEQ_DB_FILE_NAME) )
    curSeq = db.execSqlGetValue (srcObj.cName , columnSeq)
    if curSeq:
        columnStart = curSeq
    db.close()


    if isSQL:
        isSQL = isSQL.replace (config.QUERY_SEQ_TAG_VALUE, str (columnStart)).replace (config.QUERY_SEQ_TAG_FIELD, str (columnSeq))
    else:
        tblName    = srcObj.objName
        if srcMapping:
            isSQL = "Select "+",".join (srcMapping)+" From "+tblName+" Where "+str(columnSeq)+" > "+str(columnStart)
        else:
            isSQL = "Select " + "*" + " From " + tblName + " Where " + str(columnSeq) + " > " + str(columnStart)

    p("loader->addSeq: Sequence is ON, field %s, start from %s, file is update, sql: %s" % (str(columnSeq),str(columnStart),str(isSQL)), "ii")
    return isSQL, columnSeq, columnStart
##############   Not in used - need to check            #####################################