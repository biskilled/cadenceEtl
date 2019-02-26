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
    connIsSrc       = "isSource"
    partitionCol    = "column"
    partitionAgg    = "agg"
    partitionStart  = "start"

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
        inc : ['inc', 'incremental']
    }