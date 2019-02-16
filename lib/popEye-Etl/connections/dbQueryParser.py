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

import sqlparse
from sqlparse.sql       import IdentifierList, Identifier
from sqlparse.tokens    import Keyword, DML

from lib.popeye.config      import config
from lib.popeye.glob.glob   import p

def is_subselect(parsed):
    if not parsed.is_group:
        return False
    for item in parsed.tokens:
        if item.ttype is DML and item.value.upper() == 'SELECT':
            return True
    return False

def extract_from_part(parsed):
    from_seen = False
    for item in parsed.tokens:
        #print str (item.ttype) + ","  + " , " + str (item.is_group) + " ; " + str (item)
        if item.is_group:
            for x in extract_from_part(item):
                yield x
        if from_seen:
            if is_subselect(item):
                for x in extract_from_part(item):
                    yield x
            elif item.ttype is Keyword and item.value.upper() in ['ORDER', 'GROUP', 'BY', 'HAVING']:
                from_seen = False
                StopIteration
            else:
                yield item
        if item.ttype is Keyword and item.value.upper() == 'FROM':
            from_seen = True

def extract_select_part (parsed):
    allColumnSign       = config.QUERY_ALL_COLUMNS_KEY
    nonColumnSign       = config.QUERY_COLUMNS_KEY
    targetColumnNames   = config.QUERY_TARGET_COLUMNS
    columnList          = []
    columnDic           = {allColumnSign:[],targetColumnNames:[]}
    col                 = None
    addToken            = False

    for item in parsed.tokens:
        # print item.value + "  ;  " +str (item.ttype)
        if item.ttype is DML and item.value.upper() == 'SELECT':
            addToken = True

        elif item.ttype is Keyword and item.value.upper() == 'FROM':
            addToken = False
            break
        else:
            if addToken:
                dicKey  = None
                dicValue= None

                if isinstance(item, IdentifierList):
                    for identifier in item.get_identifiers():
                        identifier = str(identifier)
                        srcName = identifier

                        if identifier.lower().find(" as") > 0:
                            srcName = identifier[:identifier.lower().find(" as")].strip()
                            tarName = identifier[identifier.lower().find(" as")+3:].strip()
                        else:
                            tarName = srcName
                        columnList.append( (srcName.split(".") , tarName) )
                elif isinstance(item, Identifier):
                    item = str(item)
                    srcName = item
                    if item.lower().find(" as") > 0:
                        srcName = item[:item.lower().find(" as")].strip()
                        tarName = item[item.lower().find(" as")+3:].strip()
                    else:
                        tarName = srcName
                    columnList.append( (srcName.split(".") , tarName) )

    for tupCol in columnList:
        col     = tupCol[0]
        tarName = tupCol[1]
        if col and len (col) == 2:
            dicKey = col[0]
            dicValue = col[0]+"."+col[1]
            if dicKey not in columnDic:
                columnDic[dicKey] = []

        elif col and len (col) == 1:
            dicKey = nonColumnSign
            dicValue = col[0]
        else:
            p("queryParser->extract_select_part: ERROR Loading column identifier, will ignore column %s" % str(col), "i")
            continue

        columnDic[allColumnSign].append( dicValue )
        columnDic[targetColumnNames].append (tarName)
        if dicKey and dicKey not in columnDic:
                columnDic[dicKey] = []
        columnDic[dicKey].append (dicValue)

    return columnDic

def extract_table_identifiers(token_stream):
    for item in token_stream:
        if isinstance(item, IdentifierList):
            for identifier in item.get_identifiers():
                value = ( identifier.get_alias() , identifier._get_first_name(), identifier.get_real_name())
                value = [x.replace('"', '').replace("'", "") if x else None for x in  value]
                value = tuple( value )
                yield value

        elif isinstance(item, Identifier):
            value = (item.get_alias(), item._get_first_name(), item.get_real_name())
            value = [x.replace('"', '').replace("'", "") if x else None for x in value]
            value = tuple(value)
            yield value

def extract_tables(sql):
    # let's handle multiple statements in one sql string
    extracted_tables = []
    extracted_last_tables_Tuple = None
    extracted_last_columns_Dic = None
    statements = list(sqlparse.parse(sql))

    for statement in statements:
        if statement.get_type() != 'UNKNOWN':
            stream = extract_from_part(statement)
            # will get only last table column definistion !
            extracted_last_columns_Dic  = extract_select_part(statement)
            extracted_last_tables_Tuple = list (extract_table_identifiers(stream))
            #extracted_tables.append(list(extract_table_identifiers(stream)))
    #return list(itertools.chain(*extracted_tables))
    return (extracted_last_tables_Tuple , extracted_last_columns_Dic)

def extract_tableAndColumns (sql):
    ret = {}
    tblTupe , columns = extract_tables(sql)

    if config.QUERY_ALL_COLUMNS_KEY in columns:
        ret[config.QUERY_ALL_COLUMNS_KEY] = columns[config.QUERY_ALL_COLUMNS_KEY]
    if config.QUERY_TARGET_COLUMNS in columns:
        ret[config.QUERY_TARGET_COLUMNS] = columns[config.QUERY_TARGET_COLUMNS]
    # merge table to columns

    for tbl in tblTupe:
        alias       = tbl[0]
        schamenName = tbl[1]
        tableName   = tbl[2]

        if tableName not in ret:
            ret[tableName] = {'alias':alias, 'schema':None if schamenName==tableName else schamenName}

        if columns and len (columns)>0:
            ret[tableName]['column'] = []

        for col in columns:
            if str(col) in [tableName,alias]:
                ret[tableName]['column'].extend  (columns[col])
            if str(col) == config.QUERY_COLUMNS_KEY:
                ret[tableName]['column'].extend (columns[col])

    return ret