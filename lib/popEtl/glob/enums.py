class eDbType (object):
    SQL     = "sqlserver"
    ORACLE  = "oracle"
    VERTIVA = "vertica"
    ACCESS  = "access"
    MYSQL   = "mysql"
    FILE    = "file"

    def isExsists (prop):
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




print (eDbType.isExsists (prop="SqlServer"))