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
import logging
from popEtl.glob.enums import eDbType

class config:
    #########################   Feild per model ##############################################
    CONNECTIONS_ACTIVE      = {eDbType.SQL: "cnDb", eDbType.ORACLE: "cnDb", eDbType.MYSQL: "cnDb", eDbType.VERTIVA: "cnDb", eDbType.LITE: "cnDb", eDbType.FILE: "cnFile"}

    DIR_DATA    = ""
    CONN_URL    =  {    'sql'    :"DRIVER={SQL Server};SERVER=server,1433;DATABASE=database;UID=uid;PWD=pass;",
                        'oracle' :"DRIVER={SQL Server};SERVER=server,1433;DATABASE=database;UID=uid;PWD=pass;",
                        'mysql'  :"host=host, user=user, passwd=pass, db=db",
                        'vertica':"DRIVER=HPVertica;SERVER=server;DATABASE=database;PORT=5433;UID=user;PWD=pass",
                        'file'   :{'delimiter':',','header':True, 'folder':""}
                   }

    # Sql table configurations
    TABLE_HISTORY       = True

    RESULT_ARRAY_SIZE   = 200000
    #INSERT_CHUNK_SIZE   = 200
    TO_TRUNCATE         = True
    RESULT_LOOP_ON_ERROR= True

    # file configuration unicode
    FILE_MIN_SIZE       = 1024
    FILE_DEF_COLUMN_PREF= 'col_'
    FILE_DECODING       = "windows-1255"
    FILE_ENCODING       = "utf8"
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
    FILES_INCLUDE     = []

    NUM_OF_PROCESSES        = 1
    NUM_OF_LOADING_THREAD   = 1

    DATA_TYPE = \
    {'varchar'  :{'sql':'varchar',                      'oracle':('varchar','varchar2'),'mysql':'varchar',      'vertica':'varchar',"sqlite":'varchar' },
     'v'        :{'sql':'varchar',                      'oracle':('varchar','varchar2'),'mysql':'varchar',      'vertica':'varchar',"sqlite":'varchar'},
     'nv'       :{'sql':'nvarchar',                     'oracle':'nvarchar2',           'mysql':'nvarchar',     'vertica':'varchar',"sqlite":'varchar'},
     'nvarchar' :{'sql': 'nvarchar',                    'oracle':'nvarchar2',           'mysql':'nvarchar',     'vertica':'varchar', 'access':'text',"sqlite":'varchar'},
     'dt'       :{'sql':('smalldatetime','datetime'),   'oracle':('date','datetime'),   'mysql':'datetime',     'vertica':'timestamp',"sqlite":'varchar'},
     'bint'     :{'sql':('bigint'),                     'oracle':'number(19)',"sqlite":'int'},
     'int'      :{'sql':'int',                          'oracle':('int','float'),       'mysql':('int'),"sqlite":'int'},
     'tinyint'  :{'sql':'int',                          'oracle':'smallint',            'mysql':('tinyint'),"sqlite":'int'},
     'i'        :{'sql':'int',"sqlite":'int'},
     'numeric'  :{'sql':'numeric',                      'oracle':'number',"sqlite":'float'},
     'decimal'  :{'sql':'decimal',                      'oracle':'decimal',                                                      'mysql':'decimal',"sqlite":'decinal'},
     'cblob'    :{'sql': 'nvarchar(MAX)',               'oracle': 'clob',"sqlite":'nvarchar(MAX)'    },
     'default'  :{'sql':'varchar(100)',                 'oracle':'nvarchar(100)',                                                   'file':'varchar(100)',"sqlite":'varchar(100)'},
     'schema'   :{'sql':'dbo',                          'oracle':None,                                                                  'access':'text',"sqlite":'dbo'},
     'null'     :{'sql':'NULL',                         'oracle':'NULL',                                                            'file':'NULL',"sqlite":'NULL'},
     'sp'       :{'sql':{'match':r'([@].*[=])(.*?(;|$))', 'replace':r"[=;@\s']"}},
     'colFrame' :{'sql':("[","]"), 'oracle':("\"","\""), 'access':("[","]"), 'file':('',''), "sqlite":("[","]")}
    }

    PARSER_SQL_MAIN_KEY = "popEtl"
    PARSER_FILE_ENCODE  = "windows-1255"

    #LOGGING Properties
    LOGS_DEBUG = logging.DEBUG
    LOGS_DIR   = None
    LOGS_INFO_NAME = 'log'
    LOGS_ERR_NAME  = 'log'
    LOGS_TMP_NAME  = 'lastLog'

    #SMTP Configuration
    SMTP_SERVER             = ""
    SMTP_SERVER_USER        = ""
    SMTP_SERVER_PASS        = ""
    SMTP_SENDER             = ""
    SMTP_RECEIVERS          = ['info@biSkilled.com']


###################################################################################################################################
