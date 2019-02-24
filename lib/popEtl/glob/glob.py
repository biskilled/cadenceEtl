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
import datetime
import logging
from collections import OrderedDict

from popEtl.glob.enums import eConnValues, eDbType, ePopEtlProp
#logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
# filename='app.log', filemode='w',
#logging.warning('This will get logged to a file')


from  popEtl.config import config

def get_logger(
        LOG_FORMAT     = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        LOG_NAME       = '',
        LOG_DIR        = None,
        LOG_FILE_INFO  = 'file.log',
        LOG_FILE_ERROR = 'file.err'):

    LOG_FILE_INFO = os.path.join (LOG_DIR, LOG_FILE_INFO) if LOG_DIR else None
    LOG_FILE_INFO = os.path.join(LOG_DIR, LOG_FILE_INFO) if LOG_DIR else None

    log           = logging.getLogger(LOG_NAME)
    log_formatter = logging.Formatter(LOG_FORMAT)

    # comment this to suppress console output
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    log.addHandler(stream_handler)

    if LOG_FILE_INFO and len(LOG_FILE_INFO)>0:
        file_handler_info = logging.FileHandler(LOG_FILE_INFO, mode='w')
        file_handler_info.setFormatter(log_formatter)
        file_handler_info.setLevel(logging.INFO)
        log.addHandler(file_handler_info)

    if LOG_FILE_ERROR and len (LOG_FILE_ERROR)>0:
        file_handler_error = logging.FileHandler(LOG_FILE_ERROR, mode='w')
        file_handler_error.setFormatter(log_formatter)
        file_handler_error.setLevel(logging.ERROR)
        log.addHandler(file_handler_error)

    log.setLevel(logging.INFO)

    return log

def p(msg, ind='I'):
    logg = get_logger(LOG_DIR=None)
    ind = ind.upper()
    indPrint = {'E': 'ERROR>> ',
                'I': 'Information>> ',
                'II': 'Info>> ',
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
                logg.debug("\r" + indPrint[ind] + msg)
            elif 'II' in ind:
                logg.info(indPrint[ind] + msg)
            elif 'I' in ind:
                logg.warning(indPrint[ind] + msg)
            else:
                logg.error(indPrint[ind] + msg)

def setQueryWithParams(query):
    qRet = ""
    if query and len (query)>0:
        if isinstance(query, (list,tuple)):
            for q in query:
                #q = str(q, 'utf-8')
                for param in config.QUERY_PARAMS:
                    if param in q:
                        q = q.replace(param, config.QUERY_PARAMS[param])
                        p("config->setQueryWithParams: replace param %s with value %s, sql: %s " % (str(param), str(config.QUERY_PARAMS[param]), str (q)), "ii")
                qRet += q
        else:
            #query= str (query, 'utf-8')

            for param in config.QUERY_PARAMS:
                if param in query:
                    query = query.replace(param, config.QUERY_PARAMS[param])
                    p("config->setQueryWithParams: replace param %s with value %s, sql: %s " % (str(param), str(config.QUERY_PARAMS[param]), str(query)), "ii")
            qRet += query
    else:
        qRet = query
    return qRet

def replaceStr (sString,findStr, repStr, ignoreCase=True):
    if ignoreCase:
        pattern = re.compile(re.escape(findStr), re.IGNORECASE)
        res = pattern.sub (repStr, sString)
    else:
        res = sString.replace (findStr, repStr)
    return bytes (res, 'utf8')

def decodeStrPython2Or3 (sObj, un=True):
    pVersion = sys.version_info[0]

    if 3 == pVersion:
        return sObj
    else:
        if un:
            return unicode (sObj)
        else:
            return str(sObj).decode("windows-1255")

def setDicConnValue (connJsonVal=None, connType=None, connName=None, connObj=None, connFilter=None, connUrl=None, extraConnVal=None, isSql=False, isTarget=False, isSource=False):
    retVal = {eConnValues.connName:connName,
              eConnValues.connType:connType.lower(),
              eConnValues.connUrl:connUrl,
              eConnValues.connUrlExParams:extraConnVal,
              eConnValues.connObj:connObj,
              eConnValues.connFilter:connFilter,
              eConnValues.connIsSql:isSql,
              eConnValues.connIsSrc:isSource,
              eConnValues.connIsTar:isTarget}

    if isinstance( connJsonVal, (tuple,list) ):
        if len (connJsonVal) == 1:
            retVal[eConnValues.connName] = connJsonVal[0]
        elif len (connJsonVal) >= 2:
            retVal[eConnValues.connName] = connJsonVal[0]
            retVal[eConnValues.connObj]  = connJsonVal[1]
            if retVal[eConnValues.connType] is None:
                retVal[eConnValues.connType] = connJsonVal[0].lower()
            if len (connJsonVal) == 3:
                retVal[eConnValues.connFilter]= connJsonVal[2]
        else:
            p("glob->_setDicConnValue: Connection paramter is not valid %s must have 1,2 or 3 params: %s " %(str(connJsonVal), "e"))
            return None

        if retVal[eConnValues.connName] is None:
            p("glob->_setDicConnValue: Connection Name is not defined: %s " %(connJsonVal))
            return None

        if retVal[eConnValues.connUrl] is None:
            if retVal[eConnValues.connName] in config.CONN_URL:
                connUrl = config.CONN_URL[ retVal[eConnValues.connName] ]
                retVal[eConnValues.connUrl] = connUrl
                if isinstance(connUrl, (dict, OrderedDict) ):
                    if eConnValues.connType in connUrl:
                        retVal[eConnValues.connType] = connUrl[eConnValues.connType].lower()
                    if eConnValues.connUrl in connUrl:
                        retVal[eConnValues.connUrl] = connUrl[eConnValues.connUrl]
            else:
                p("glob->_setDicConnValue: Connection Name is not defined in CONN_URL config. define names are : %s  "  %(str(list(config.CONN_URL.keys()))))
                return None
        # remove number from connection type in case we used it in config.CONN_URL
        # sample : sql1 - will be rename to sql as a type
        retVal[eConnValues.connType] = ''.join([i for i in retVal[eConnValues.connType].lower() if not i.isdigit()])

        # For access - add paramters
        if eDbType.ACCESS == retVal[eConnValues.connType] and retVal[eConnValues.connUrlExParams] is not None:
            retVal[eConnValues.connUrl] = retVal[eConnValues.connUrl][0] % (retVal[eConnValues.connUrl][1] + str(retVal[eConnValues.connUrlExParams].split(".")[0] + ".accdb"))

        retVal[eConnValues.connType] = eDbType.isExsists( retVal[eConnValues.connType] )

        if  retVal[eConnValues.connName] is not None and \
            retVal[eConnValues.connType] is not None and \
            retVal[eConnValues.connObj] is not None and \
            retVal[eConnValues.connUrl] is not None:
                p ("glob->_setDicConnValue: Connection params: %s " %(str(retVal)),"ii")
                return retVal
        else:
            p("glob->_setDicConnValue: Connection params are not set: %s " % (str(retVal)), "e")
        return None

def getDicKey (etlProp, allProp):
    if etlProp in ePopEtlProp.dicOfProp:
        etlProps = ePopEtlProp.dicOfProp[ etlProp ]

        filterSet = set (etlProps)
        allSet    = set (allProp)

        isExists = filterSet.intersection(allSet)

        if len (isExists) > 0:
            return isExists.pop()
    return None

