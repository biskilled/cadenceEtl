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

import re
import sys
import os
import io
import datetime
import logging
from collections import OrderedDict

from popEtl.glob.enums import eConnValues, eDbType, ePopEtlProp, isDbType
from  popEtl.config import config

def getLogger (
    LOG_FORMAT     = '%(asctime)s %(levelname)s %(message)s',
    LOG_DIR        = None,
    LOG_FILE       = 'file',
    LOGS_DEBUG      = logging.DEBUG
    ):

    #logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logFormatter= logging.Formatter(LOG_FORMAT)
    logg  = logging.getLogger()

    if LOG_DIR:
        fileHandler = logging.FileHandler("{0}/{1}.log".format(LOG_DIR, LOG_FILE))
        fileHandler.setFormatter(logFormatter)
        logg.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    logg.addHandler(consoleHandler)

    logg.setLevel( LOGS_DEBUG )

    return logg

logg = getLogger (LOGS_DEBUG=config.LOGS_DEBUG)
def p(msg, ind='I'):
    ind = ind.upper()
    indPrint = {'E': 'ERROR>> ',
                'I': 'INFO >> ',
                'II': 'DEBUG>> ',
                'III': 'Progress>> '}
    allowToPrint    = ['E', 'I','II', 'III']  #  'II', 'III'
    #allowToPrint = ['E','I']
    allowToSaveInDB_E = ['E']
    allowToSaveInDB_I = ['I']
    allowToSaveInDB = allowToSaveInDB_E + allowToSaveInDB_I

    if ind in allowToPrint or (config.LOGS_IN_DB and ind in allowToSaveInDB):
        localTime = datetime.datetime.today()
        if config.LOGS_IN_DB and ind in allowToSaveInDB_E:
            timeStr = localTime.strftime("%m/%d/%Y %H:%M:%S")
            config.LOGS_ARR_E.append((timeStr,config.LOGS_DB_TIME_STEMP, ind, str(msg)))
        elif config.LOGS_IN_DB and ind in allowToSaveInDB_I:
            timeStr = localTime.strftime("%m/%d/%Y %H:%M:%S")
            config.LOGS_ARR_I.append((timeStr,config.LOGS_DB_TIME_STEMP, ind, str(msg)))
        if config.LOGS_PRINT and ind in allowToPrint:
            timeStr = localTime.strftime("%d/%m/%Y %H:%M:%S")
            if 'III' in ind:
                logg.debug("\r %s %s" %(indPrint[ind], msg))
            elif 'II' in ind:
                logg.debug("%s %s" %(indPrint[ind], msg))
            elif 'I' in ind:
                logg.info("%s %s" %(indPrint[ind], msg))
            else:
                logg.error(str(indPrint[ind]) + str(msg))

def setQueryWithParams(query):
    qRet = ""
    if query and len (query)>0:
        if isinstance(query, (list,tuple)):
            for q in query:
                #q = str(q, 'utf-8')
                for param in config.QUERY_PARAMS:
                    q = replaceStr(sString=q, findStr=param, repStr=config.QUERY_PARAMS[param], ignoreCase=True, addQuotes="'")
                    #if param in q:
                    #    q = q.replace(param, config.QUERY_PARAMS[param])
                    p("glob->setQueryWithParams: replace param %s with value %s" % (str(param), str(config.QUERY_PARAMS[param])), "ii")
                qRet += q
        else:
            #query= str (query, 'utf-8')

            for param in config.QUERY_PARAMS:
                if param in query:
                    query = replaceStr(sString=query, findStr=param, repStr=config.QUERY_PARAMS[param], ignoreCase=True,addQuotes="'")
                    p("glob->setQueryWithParams: replace param %s with value %s ..." % (str(param), str(config.QUERY_PARAMS[param])), "ii")
            qRet += query
    else:
        qRet = query
    return qRet

def replaceStr (sString,findStr, repStr, ignoreCase=True,addQuotes=None):
    if addQuotes and isinstance(repStr,str):
        repStr="%s%s%s" %(addQuotes,repStr,addQuotes)

    if ignoreCase:
        pattern = re.compile(re.escape(findStr), re.IGNORECASE)
        res = pattern.sub (repStr, sString)
    else:
        res = sString.replace (findStr, repStr)
    return res

def decodeStrPython2Or3 (sObj, un=True):
    pVersion = sys.version_info[0]

    if 3 == pVersion:
        return sObj
    else:
        if un:
            return unicode (sObj)
        else:
            return str(sObj).decode("windows-1255")

def getDicKey (etlProp, allProp):
    etlProp = str(etlProp).lower() if etlProp else ''

    if etlProp in ePopEtlProp.dicOfProp:
        etlProps = ePopEtlProp.dicOfProp[ etlProp ]

        filterSet = set (etlProps)
        allSet    = set ([str(x).lower() for x in allProp])
        isExists = filterSet.intersection(allSet)

        if len (isExists) > 0:
            return isExists.pop()
    return None

def filterFiles (modelToExec, dirData=None, includeFiles=None, notIncludeFiles=None ):
    dirData          = dirData if dirData else config.DIR_DATA
    notIncludeFiles = notIncludeFiles if notIncludeFiles else config.FILES_NOT_INCLUDE
    notIncludeFilesL=[x.lower().replace(".json","") for x in notIncludeFiles]
    includeFiles    = includeFiles if includeFiles else config.FILES_INCLUDE

    jsonFiles = [pos_json for pos_json in os.listdir(dirData) if pos_json.endswith('.json')]

    jsonFilesDic    = {x.lower().replace(".json",""):x for x in jsonFiles}



    if  notIncludeFiles:
        notIncludeDict = {x.lower().replace(".json", ""): x for x in notIncludeFiles}
        for f in jsonFilesDic:
            if f in notIncludeDict:
                p('%s: NOT INCLUDE: Folder:%s, file: %s NOT IN USED, REMOVED >>>>' % (modelToExec, str(config.DIR_DATA), f),"ii")
                jsonFiles.remove( jsonFilesDic[f] )
        for f in notIncludeDict:
            if f not in jsonFilesDic:
                p('%s: NOT INCLUDE: Folder: %s, file: %s not exists.. Ignoring>>>>>' % (modelToExec, str(config.DIR_DATA), f), "ii")

    if  includeFiles:
        includeDict = {x.lower().replace(".json", ""): x for x in includeFiles}
        for f in jsonFilesDic:
            if f not in includeDict:
                p('%s: INCLUDE: Folder:%s, file: %s NOT IN USED, REMOVED >>>>'% (modelToExec, str(config.DIR_DATA), f), "ii")
                jsonFiles.remove( jsonFilesDic[f] )
        for f in includeDict:
            if f not in jsonFilesDic:
                p('%s: INCLUDE: Folder: %s, file: %s not exists.. Ignoring >>>>' % (modelToExec, str(config.DIR_DATA), f), "ii")

    return jsonFiles

class validation (object):
    def __init__ (self):
        pass

    @property
    def CON_DIR_DATA(self):
        return config.DIR_DATA

    @CON_DIR_DATA.setter
    def CON_DIR_DATA(self, val):
        if not os.path.isdir(val):
            err = "%s is not a folder !" %(str(val))
            raise ValueError(err)
        config.DIR_DATA=val

    @property
    def CONNECTION_URL(self):
        return config.CONN_URL

    @CONNECTION_URL.setter
    def CONNECTION_URL(self,val):
        if isinstance(val, dict):
            for v in val:
                dbType = isDbType(v)
                if not dbType:
                    if isinstance(val[v], dict) and eConnValues.connType in val[v] and isDbType( val[v][eConnValues.connType] ) is not None:
                        pass
                    else:
                        err = "%s:, %s is not legal Conn type !" %(str(v),str(val[v]))
                        raise ValueError(err)
            for v in val:
                config.CONN_URL[v] = val[v]
        else:
            raise ValueError("Value must be dicionary !")

    @property
    def TABLE_HISTORY(self):
        return config.TABLE_HISTORY
    @TABLE_HISTORY.setter
    def TABLE_HISTORY(self, val):
        if val==True or val==False:
            config.TABLE_HISTORY = val
        else:
            raise ValueError("Value must be True or False !")

    @property
    def TO_TRUNCATE(self):
        return config.TO_TRUNCATE

    @TO_TRUNCATE.setter
    def TO_TRUNCATE(self, val):
        if val == True or val == False:
            config.TO_TRUNCATE = val
        else:
            raise ValueError("Value must be True or False !")

    @property
    def RESULT_LOOP_ON_ERROR(self):
        return config.RESULT_LOOP_ON_ERROR

    @RESULT_LOOP_ON_ERROR.setter
    def RESULT_LOOP_ON_ERROR(self, val):
        if val == True or val == False:
            config.RESULT_LOOP_ON_ERROR = val
        else:
            raise ValueError("Value must be True or False !")

    @property
    def LOGS_IN_DB(self):
        return config.LOGS_IN_DB

    @LOGS_IN_DB.setter
    def LOGS_IN_DB(self, val):
        if val == True or val == False:
            config.LOGS_IN_DB = val
        else:
            raise ValueError("Value must be True or False !")

    @property
    def FILES_NOT_INCLUDE(self):
        return config.FILES_NOT_INCLUDE

    @FILES_NOT_INCLUDE.setter
    def FILES_NOT_INCLUDE(self, val):
        config.FILES_NOT_INCLUDE = val

    @property
    def FILES_INCLUDE(self):
        return config.FILES_INCLUDE

    @FILES_INCLUDE.setter
    def FILES_INCLUDE(self, val):
        config.FILES_INCLUDE = val

    @property
    def QUERY_PARAMS(self):
        return config.QUERY_PARAMS

    @QUERY_PARAMS.setter
    def QUERY_PARAMS(self, val):
        if isinstance(val, (dict, OrderedDict ) ):
            config.QUERY_PARAMS = val
        else:
            err = "param must be dictionary: %s" %(str(val))
            raise ValueError(err)
