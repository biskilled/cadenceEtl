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

from config                  import config
from glob.glob               import p, setQueryWithParams
from connections.dbSqlLite   import sqlLite
from connections.connector   import connector
from glob.globalDBFunctions  import logsToDb

# Will merge table with connection in source object
def execMerge (dst, merge, sttDic, toCreate=True):
    mergeKeys = None
    if isinstance( merge , (list,tuple) ):
        mergeTable = merge[0]
        mergeKeys   = merge[1]
    else:
        mergeTable = merge

    dstObj = connector(dst)
    # create target table same as source one
    if toCreate:
        dstObj.create (stt=sttDic, tblName=mergeTable )

    dstObj.merge (mergeTable=mergeTable, mergeKeys=mergeKeys)
    dstObj.close()

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

def appendPartitions (src, partition):
    srcName = src[1]
    ret = []
    sqlStart = "SELECT * FROM %s WHERE " %(srcName)
    if 'column' in partition:
        colToFilter = partition['column']
    else:
        p("loader->appendPartitions: There is partition without column definition table: %s ..." % (srcName), "e")
        return ret

    if 'agg' in partition:
        resolution = partition['agg']
        srcObj = connector(src)

        # Set starting from partition
        if 'start' in partition:
            minDate = srcObj.minValues (resolution=resolution, periods=partition['start'])
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
    else:
        p ("loader->appendPartitions: There is partition without aggragation function, needs to have 'agg' with values of 'd', 'm' or 'y', table: %s ..." %(str (src)) , "e")
    return ret

# jMap, src, dst
def execTarget (dst):
    dstConn = dst

    if config.TO_TRUNCATE or len(dstConn) == 3:
        dstObj = connector(dstConn)

        # there is delete from destintation table
        if len(dstConn) == 3:
            sql = "Delete From "+dstObj.cName+" Where "+dstConn[2]
            sql = setQueryWithParams (sql)
            p ("loader->execTarget: Destination %s have delete query %s, deleting target " %(dstObj.cName, sql),"ii")
            dstObj.execSP(sql)
        else:
            if config.TO_TRUNCATE:
                p("loader->execTarget: Destination %s is trancating  " % (dstObj.cName),"ii")
                dstObj.truncate()
        dstObj.close()

def updateSourceTargetCompareLog (js):
    isRepoTblsExists  = False
    connUrl     = None
    connType    = None

    with open(os.path.join(config.DIR_DATA, js)) as jsonFile:
        jText = json.load(jsonFile, object_pairs_hook=OrderedDict)

    p("loader->updateSourceTargetCompareLog: Loading from file %s COMPARE number of rows in Source vs target " % (str(js)),"i")
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
def execLoading ( params ):
    (src, dst, sttDic, isSql, merge, js, cProc, tProc) = params
    p("loader->execLoading: loading %s out of %s, src: %s, dst: %s " %(str(cProc), str(tProc), str(src), str(dst)), "i")
    # Managing Destination table
    execTarget(dst=dst)

    # True / false indication
    addSourceColumn = False
    if sttDic and config.STT_INTERNAL in sttDic:
        addSourceColumn = sttDic[config.STT_INTERNAL]
        del sttDic[config.STT_INTERNAL]

    if "access" in src[0]:
        accessFilePath = config.CONN_URL["access"][0] % (config.CONN_URL["access"][1] + str(js.split(".")[0] + ".accdb"))
        srcObj = connector(connProp=src, connUrl=accessFilePath,isSql=isSql)
    else:
        srcObj = connector(connProp=src, isSql=isSql)

    # Check if source is same as target connection (only for merge option)
    if  set([tuple(lst) for lst in src]) != set([tuple(lst) for lst in dst]):
        # load all source data
        sttDic = srcObj.structure(stt=sttDic,addSourceColumn=addSourceColumn)
        # isSQL, columnInc, columnStart = addIncemenral (inc, isSQL, srcObj, srcMapping)
        srcObj.toDB (dst=dst, stt=sttDic )

    else:
        p('loader->execLoading: SOURCE %s and TARGET %s object are identical.. will check if there is merge >>>>>' % ( str(src), str(dst) ), "ii")

    if merge:
        execMerge (dst=dst, merge=merge, sttDic=None, toCreate=True)

    srcObj.close()
    if config.LOGS_IN_DB : logsToDb( str(js)+":"+str(dst) )

def loading (sourceList=None, destList=None):
    # multiprocessing.freeze_support()
    p('loader->loading: Start mapping data from Folder %s >>>>>' % (config.DIR_DATA), "i")
    jsonFiles = [pos_json for pos_json in os.listdir(config.DIR_DATA) if pos_json.endswith('.json')]
    for f in list(jsonFiles):
        if f in config.FILES_NOT_INCLUDE:   jsonFiles.remove(f)
    toLoad      = True
    loadedObject= []
    processList = []

    for index, js in enumerate(jsonFiles):
        with io.open(os.path.join(config.DIR_DATA, js), encoding="utf-8") as jsonFile:           #
            jText = json.load(jsonFile, object_pairs_hook=OrderedDict)

        processList = list([])
        cProc       = 0
        p("loader->loading: Start loading from file %s >>>>>>" %(str(js)), "i")
        sTime = time.time()
        for jMap in jText:
            keys        = [x.lower() for x in jMap.keys()]
            dst         = {'target', 'tar'}.intersection(set(keys))
            src         = {'source','src'}.intersection(set(keys))
            query       = {'query'}.intersection(set(keys))
            mapping     = {'mapping', 'map'}.intersection(set(keys))
            partition   = {'partition'}.intersection(set(keys))
            merge       = {'merge'}.intersection(set(keys))
            inc         = {'inc' , 'incremental'}.intersection(set(keys))
            seq         = {'seq'}.intersection(set(keys))
            stt         = {'stt', 'sttappend'}.intersection(set(keys))
            sttDic      = None


            # exists source/query AND destination OR destination and merge only
            if len(dst)>0 and (len(src)>0 or len(query)>0) or ( len(merge)>0 and len(dst)>0 )  :
                merge   = jMap[merge.pop()]     if len(merge)>0     else None
                seq     = jMap[seq.pop()]       if len(seq)>0       else None
                inc     = jMap[inc.pop()]       if len(inc)>0       else None
                query   = query.pop()           if len (query)>0    else None
                mapping = jMap[mapping.pop()]   if len(mapping)>0   else None
                stt     = stt.pop()             if len(stt)>0       else None
                sttDic  = jMap[stt]             if stt              else None
                isSql   = True                  if query            else False
                partition = jMap[partition.pop()] if len(partition) > 0 else None

                # will use dst if exists. if not-> will use source if exists, if not will use query                                 dst->src->query
                dst     = dst.pop() if len(dst)>0 else src.pop() if len(src)>0 else query
                src     = src.pop() if len(src)>0 else query if query else dst

                dst     = jMap[dst]
                src     = jMap[src]

                srcType = src[0]
                srcName = src[1]
                dstType = dst[0]
                dstName = src[1] if len(dst) < 2 else dst[1]

                #update sttDic with mapping -> if exists
                if mapping:
                    if sttDic:
                        sttDicTemp = sttDic
                        sttDic = OrderedDict()
                        for t in mapping:
                            if t in sttDicTemp:
                                sttDic[t] = sttDicTemp[t]
                                if "s" not in sttDic[t]:
                                    sttDic[t]["s"] = mapping[t]
                            else:
                                sttDic[t] = {"s":mapping[t]}
                        for t in sttDicTemp:
                            if t not in sttDic: sttDic[t] = sttDicTemp[t]
                    else:
                        sttDic = OrderedDict()
                        for t in mapping:
                            sttDic[t] = {"s": mapping[t]}

                sttDic = sttDic if sttDic and len(sttDic)>0 else None
                # Update sttDic
                if sttDic:  sttDic[config.STT_INTERNAL] = True if stt and "append" in stt and not mapping else False


                toLoad  = True if not sourceList or (sourceList and srcName in (sourceList)) else False
                toLoad  = True if not destList or (destList and dstName in (destList)) else False

                if toLoad:
                    p('loader->loading: Loading source type %s, source name %s into destination type: %s, destination name %s >>>>>' % (str(srcType), srcName, str(dstType), dstName), "ii")
                    # if partition --> change to all partitions
                    # update list of data to process:
                    if partition:
                        if inc:
                            p('loader->loading: Cannot have incremental and partiton loading methods.. will use partiton method >>>>>' , "ii")
                        if not query or len(query)<1:
                            newSqlList = []
                            newSqlList = appendPartitions (src,  partition)
                            for newSql in newSqlList:
                                processList.append( ([srcType,newSqlList], dst, sttDic, True, merge,js, cProc) )
                                cProc +=1
                            loadedObject.append ("PARTITION "+dstName+" !!!! ")
                        else:
                            p('loader->loading: Cannot have partition with query as source.. will use query as is, sql: %s >>>>>' % (str(srcName)), "ii")
                            processList.append ( (src, dst, sttDic, isSql, merge,js, cProc) )
                            cProc+=1
                    else:
                        processList.append ( (src, dst, sttDic, isSql, merge,js, cProc) )
                        cProc+=1
                    loadedObject.append (dstName)

            else:
                p("loader->loading: There is nothing to do >>>>>>>>>>>>>>", "i")

            eTime = (time.time() - sTime) / 60          # in minutes

        # Strat runing all processes per file
        numOfProcesses = len (processList) if len (processList) < config.NUM_OF_PROCESSES else config.NUM_OF_PROCESSES

        for i, itemP in enumerate(processList):
            processList[i] = itemP + (cProc,)

        if numOfProcesses >1:
            proc = multiprocessing.Pool(config.NUM_OF_PROCESSES).map(execLoading,processList )
        else:
            if numOfProcesses >0:
                for etl in processList:
                    execLoading ( etl )

        p("loader->loading: Finish loading from file %s >>>>>>" % (str(js)), "i")
        if config.LOGS_IN_DB: logsToDb()
        if config.LOGS_COUNT_SRC_DST: updateSourceTargetCompareLog (js)

    p("loader->loading: FINISH LOADING, Loader into : " + str (loadedObject), "i")

if __name__ == '__main__':
    multiprocessing.freeze_support()