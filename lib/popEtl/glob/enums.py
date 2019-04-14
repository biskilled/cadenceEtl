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

class eDbType (object):
    SQL     = "sql"
    ORACLE  = "oracle"
    VERTIVA = "vertica"
    ACCESS  = "access"
    MYSQL   = "mysql"
    FILE    = "file"

def isDbType (prop):
    dicClass = eDbType.__dict__
    for p in dicClass:
        if isinstance(dicClass[p], str) and dicClass[p].lower() == prop.lower():
            return prop.lower()
    return None

class eConnValues (object):
    connName        = "name"
    connType        = "type"
    connUrl         = "url"
    connUrlExParams = "urlExParams"
    connObj         = "object"
    connIsSql       = "isSql"
    connFilter      = "filter"
    connIsTar       = "isTarget"
    connIsMerge     = "isMerge"
    connIsSrc       = "isSource"
    partitionCol    = "column"
    partitionAgg    = "agg"
    partitionStart  = "start"
    fileToLoad      = "file"

    fileDelimiter   = "delimiter"
    fileHeader      = "header"
    fileFolder      = "folder"
    fileNewLine     = "newLine"
    fileEncoding    = "encoding"
    fileErrors      = "errors"

class ePopEtlProp (object):
    src = "source"
    tar = "target"
    qry = "query"
    mrg = "merge"
    add = "addSrcColumns"
    seq = "seq"
    stt = "stt"
    sttA= "sttappend"
    map = "mapping"
    col = "column"
    par = "partition"
    inc = "incremental"
    exe = "execsql"

    dicOfProp = {
        src : ["source","src"],
        tar : ["target","tar"],
        qry : ["query"],
        mrg : ["merge"],
        seq : ["seq"],
        stt : ['stt', 'sttappend'],
        map : ['mapping', 'map'],
        col : ['columns', 'column', 'col'],
        par : ['partition'],
        inc : ['inc', 'incremental'],
        exe : ['esql', 'execsql']
    }