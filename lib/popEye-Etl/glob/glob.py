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
import datetime

from lib.popeye.config import config

def p(msg, ind='I'):
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
                print("\r" + timeStr + ' ' + indPrint[ind] + msg)
            else:
                print(timeStr + ' ' + indPrint[ind] + msg)

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