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

import datetime

class config:
    #########################   Feild per model ##############################################
    CONNECTIONS_ACTIVE      = {"sql": "cnDb", "oracle": "cnDb", "mysql": "cnDb", "vertica": "cnDb", 'file': "cnFile"}

    DIR_DATA    = "C:\\Python27\\apps\\mapper\\dataTrade"
    CONN_URL    =  {      'sql'    :"DRIVER={SQL Server};SERVER=TAL-LENOVO,1433;DATABASE=bnz_namer;UID=tals;PWD=tals;",
                        'oracle' :"DRIVER={SQL Server};SERVER=TAL-LENOVO,1433;DATABASE=bnz_namer;UID=tals;PWD=tals;",
                        'mysql'  : "host=vertica-test-1.tuenti.int, user=bi, passwd=delegated3206, db=sampled_mirror_operational",
                        'vertica':"DRIVER=HPVertica;SERVER=vertica-test-1.tuenti.int;DATABASE=db1;PORT=5433;UID=dbadmin;PWD=mypassword",
                        'file'   :{'delimiter':',','header':True, 'folder':""}
                   }

    # "DRIVER={SQL Server};SERVER=JJ-TALS,1433;DATABASE=CDRDW;UID=tals;PWD=tals;"
    # "DRIVER={SQL Server};SERVER=TAL-LENOVO,1433;DATABASE=bnz_namer;UID=tals;PWD=tals;"

    # Sql table configurations
    TABLE_HISTORY       = True
    FILE_MIN_SIZE       = 1024
    FILE_DEF_COLUMN_PREF= 'col_'
    RESULT_ARRAY_SIZE   = 200000
    #INSERT_CHUNK_SIZE   = 200
    TO_TRUNCATE         = True
    RESULT_LOOP_ON_ERROR= True
    # file configuration unicode
    FILE_DECODING = "windows-1255"
    FILE_ENCODING = "utf8"
    FILE_DEFAULT_DELIMITER = ","
    FILE_DEFAULT_FOLDER = DIR_DATA
    FILE_DEFAULT_HEADER = True
    FILE_DEFAULT_NEWLINE= "\r\n"
    FILE_MAX_LINES_PARSE= 100000
    FILE_LOAD_WITH_CHAR_ERR = 'strict'    # or ignore

    # queryParser configuration
    QUERY_COLUMNS_KEY       = '~'
    QUERY_ALL_COLUMNS_KEY   = '~allcol~'
    QUERY_SEQ_TAG_VALUE     = '~seqValue~'
    QUERY_SEQ_TAG_FIELD     = '~seqField~'
    QUERY_TARGET_COLUMNS    = '~target~'
    QUERY_PARAMS            = {}
    STT_INTERNAL            = '~internal~'
    QUERY_SORT_BY_SOURCE    = True

    SEQ_DB_FILE_NAME        = 'db'
    SEQ_DEFAULT_DATA_TYPE   = 'int'
    SEQ_DEFAULT_SEQ_START   = 1
    SEQ_DEFAULT_SEQ_INC     = 1

    FILES_NOT_INCLUDE = []

    NUM_OF_PROCESSES = 1
    NUM_OF_LOADING_THREAD = 1

    SMTP_SERVER             =  "172.31.2.10" #"smtp.gmail.com:587"
    SMTP_SERVER_USER        =  "AlertBi@b-zion.org.il" #"tal@bpmk.co.il"
    SMTP_SERVER_PASS        = "bi2018"
    SMTP_SENDER             = "AlertBi@b-zion.org.il" #'tal@bpmk.co.il'
    SMTP_RECEIVERS          = ['tal@bpmk.co.il'] # Oren.Muslavi@b-zion.org.il

    DATA_TYPE = \
    {'varchar'  :{'sql':'varchar',                      'oracle':('varchar','varchar2'),'mysql':'varchar',      'vertica':'varchar', },
     'v'        :{'sql':'varchar',                      'oracle':('varchar','varchar2'),'mysql':'varchar',      'vertica':'varchar'},
     'nv'       :{'sql':'nvarchar',                     'oracle':'nvarchar2',           'mysql':'nvarchar',     'vertica':'varchar'},
     'nvarchar' :{'sql': 'nvarchar',                    'oracle':'nvarchar2',           'mysql':'nvarchar',     'vertica':'varchar', 'access':'text'},
     'dt'       :{'sql':('smalldatetime','datetime'),   'oracle':('date','datetime'),   'mysql':'datetime',     'vertica':'timestamp'},
     'bint'     :{'sql':('bigint'),                     'oracle':'number(19)'},
     'int'      :{'sql':'int',                          'oracle':('int','float'),       'mysql':('int')},
     'tinyint'  :{'sql':'int',                          'oracle':'smallint',            'mysql':('tinyint')},
     'i'        :{'sql':'int'},
     'numeric'  :{'sql':'numeric',                      'oracle':'number'},
     'decimal'  :{'sql':'decimal',                      'oracle':'decimal',                                                      'mysql':'decimal'},
     'cblob'    :{'sql': 'nvarchar(MAX)',               'oracle': 'clob'    },
     'default'  :{'sql':'varchar(100)',                 'oracle':'nvarchar(100)',                                                   'file':'varchar(100)'},
     'schema'   :{'sql':'dbo',                          'oracle':None,                                                                  'access':'text'},
     'null'     :{'sql':'NULL',                         'oracle':'NULL',                                                            'file':'NULL'},
     'sp'       :{'sql':{'match':r'([@].*[=])(.*?(;|$))', 'replace':r"[=;@\s']"}},
     'colFrame' :{'sql':("[","]"), 'oracle':("\"","\""), 'access':("[","]")}
    }

    #logs in DB
    LOGS_IN_DB          = True
    LOGS_DB_TIME_STEMP  = datetime.datetime.today()
    LOGS_PRINT          = True
    LOGS_ARR_I          = []
    LOGS_ARR_E          = []
    LOGS_COUNT_SRC_DST = False

    LOGS_DB_TBL = {"AAA_LOG_ERR":{"d":"startDate","f":["updateDate","startDate","logType","dDesc"],"t":"error","days":10},
                   "AAA_LOG_INFO": {"d": "startDate", "f": ["updateDate","startDate","logType","dDesc"],"t":"info", "days":10}
                   }

    LOGS_TBL_COUNT = "AAA_TBL_INFO"

    MSG_SEND_TABLE = {1:"Total loading in minutes ",
                      2:"Total minutes for all queryies ",
                      3:"Total minutes for all OLAP objects ",
                      'err':"ERRORS",
                      'inf':"INFO  ",
                      "subj":"Loading JOB %s ",
                      "subjERR":"ERROR : %s "}

###################################################################################################################################
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
                print("\r" + timeStr + ' ' + indPrint[ind] + msg, end='')
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
