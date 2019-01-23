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


######### SQL : RENAME TABLE
def sql_renameTable (tblName, tblNewName):
    return "EXEC sp_rename '"+tblName+"', '"+tblNewName+"'"

######### SQL : DROP TABLE
def sql_dropTable (tblName):
    return "drop table "+tblName

def oracle_dropTable (tblName):
    return "Drop table "+ tblName + ";"

######### SQL : TRUNCATE TABLE
def sql_truncate (tblName):
    return "truncate table "+tblName

def oracle_truncate (tblName):
    return "truncate table "+ tblName + ";"

######### SQL : COLUMN DEFINISTION : column name, column type
def mysql_columnDefinition (tbl):
    schema = None
    endSchema = tbl.find(".",0)
    if endSchema>0:
        schema = tbl[0:endSchema]
        tbl = tbl[endSchema+1:]
    sql = """
    SELECT distinct column_name, column_type  FROM information_schema.columns
    WHERE table_name='"""+tbl+"' "
    sql += "and TABLE_SCHEMA='"+schema+"';" if schema else ";"

    return sql

def vertica_columnDefinition (tbl):
    schema = None
    endSchema = tbl.find(".",0)
    if endSchema>0:
        schema = tbl[0:endSchema]
        tbl = tbl[endSchema+1:]
    # SELECT column_name, data_type, is_nullable FROM columns  WHERE table_schema = 'data' And table_name='historical_status_trials';
    sql = """
    SELECT distinct column_name, data_type  FROM columns
    WHERE table_name='"""+tbl+"' "
    sql += "and table_schema='"+schema+"';" if schema else ";"

    return sql

def sql_columnDefinition (tbl):
    schema = None
    endSchema = tbl.find(".",0)
    if endSchema>0:
        schema = tbl[0:endSchema]
        tbl = tbl[endSchema+1:]

    sql = """
    SELECT c.name,
    UPPER(tp.name) +
    CASE	WHEN tp.name IN ('varchar', 'char', 'varbinary', 'binary', 'text')
                THEN '(' + CASE WHEN c.max_length = -1 THEN 'MAX' ELSE CAST(c.max_length AS VARCHAR(5)) END + ')'
            WHEN tp.name IN ('nvarchar', 'nchar')
                THEN '(' + CASE WHEN c.max_length = -1 THEN 'MAX' ELSE CAST(c.max_length / 2 AS VARCHAR(5)) END + ')'
            WHEN tp.name IN ('ntext')
                THEN ''
            WHEN tp.name IN ('datetime2', 'time2', 'datetimeoffset')
                THEN '(' + CAST(c.scale AS VARCHAR(5)) + ')'
            WHEN tp.name IN ('decimal','numeric')
                THEN '(' + CAST(c.[precision] AS VARCHAR(5)) + ',' + CAST(c.scale AS VARCHAR(5)) + ')'
        ELSE ''
        END as colType

    FROM sys.columns c WITH (NOWAIT)
    JOIN sys.types tp WITH (NOWAIT) ON c.user_type_id = tp.user_type_id
    WHERE c.[object_id] =
        (Select top 1 object_id as obID from
        (SELECT SCHEMA_NAME(schema_id) schemaDesc , name , object_id FROM sys.tables
         Union
        Select SCHEMA_NAME(schema_id) schemaDesc , name , object_id FROM sys.views) tt
        Where """
    sql += "schemaDesc='"+schema.replace("[","").replace("]","")+"' and " if schema else ""
    sql+= "name='"+tbl.replace("[","").replace("]","")+"') ORDER BY c.column_id"

    return sql

def oracle_columnDefinition ( tbl ):
    schema = None
    endSchema = tbl.find(".", 0)

    if endSchema > 0:
        schema = tbl[0:endSchema]
        tbl = tbl[endSchema + 1:]

    sql = "select column_name, data_type || "
    sql += "case when data_type = 'NUMBER' and data_precision is not null then '(' | | data_precision | | ',' | | data_scale | | ')' "
    sql += "when data_type = 'NUMBER' then '(18,0)' "
    sql += "when data_type like '%CHAR%' then '(' | | data_length | | ')' "
    sql += "else '' end type "
    sql += "from all_tab_columns where table_name = '" + tbl + "' "
    sql += " and owner='" + schema + "'" if schema else ""
    sql += " ORDER BY COLUMN_ID"
    return str(sql)

######### SQL : COLUMN NAMES : column name
def sql_columnsNames (tblName, tblSchema=None):
    if not tblSchema:
        endSchema = tblName.find(".", 0)
        if endSchema > 0:
            tblSchema = tblName[0:endSchema]
            tblName = tblName[endSchema + 1:]

    if tblSchema:
        sql = "select column_name from information_schema.columns where table_name='" + tblName + "' And table_schema='" + tblSchema + "' order by ordinal_position"
    else:
        sql = "select column_name from information_schema.columns where table_name='" + tblName + "' order by ordinal_position"
    return sql

def oracle_columnsNames (tblName, tblSchema=None):
    if not tblSchema:
        endSchema = tblName.find(".", 0)
        if endSchema > 0:
            tblSchema = tblName[0:endSchema]
            tblName = tblName[endSchema + 1:]
    if tblSchema:
        sql = "select column_name from information_schema.columns where table_name='" + tblName + "' And table_schema='" + tblSchema + "' order by ordinal_position"
    else:
        sql = "select column_name from information_schema.columns where table_name='" + tblName + "' order by ordinal_position"
    return sql

######### SQL : DATABASE STRUCURE
def sql_objectStrucute (filterDic):
    typesObj    = "'BASE TABLE','VIEW'"
    likeStr     = None
    sql         = ""
    if filterDic:
        if 'type' in filterDic:
            typesObj = ",".join([ "'"+x.replace ('"','').replace("'","")+"'" for x in filterDic['type']])
        if 'like' in filterDic:
            likeStr = " TABLE_NAME like ('%"+filterDic['like'].replace("'","").replace('"','')+"%') "
    # select type_desc,type, name from sys.objects WHERE type in ( %s ) AND %s order by name
    # SELECT TABLE_SCHEMA+'.'+TABLE_NAME FROM INFORMATION_SCHEMA.TABLES Where TABLE_TYPE in ('BASE TABLE','VIEW')
    if  likeStr:
        sql = "SELECT TABLE_SCHEMA+'.'+TABLE_NAME, TABLE_TYPE FROM INFORMATION_SCHEMA.TABLES Where TABLE_TYPE in ( %s ) AND %s " %( typesObj , likeStr)
    else:
        sql = "SELECT TABLE_SCHEMA+'.'+TABLE_NAME, TABLE_TYPE FROM INFORMATION_SCHEMA.TABLES Where TABLE_TYPE in ( %s ) " % (typesObj)
    sql+=" ORDER BY TABLE_SCHEMA+'.'+TABLE_NAME"
    return sql

######### SQL : MINIMUN VALUE : tblName, tblSchema, resolution, periods, col=None, startDate=None
def sql_minValue (tblName, tblSchema, resolution,periods,col=None, startDate=None):
    sql = ""
    dDate = " getdate() "
    if startDate:
        dDate = (" Convert (smalldatetime '%s') " %str(startDate))
    if col:
        sql = "Select CONVERT (DATE, MIN (%s)) FROM " % str (col)
        if tblSchema:
            sql += tblSchema + "." + tblName
        else:
            sql += tblName
    else:
        sql = "Select convert (date, dataadd (%s, %s, %s))" %(str(resolution),str(periods),dDate)
    return sql

def mysql_minValue (tblName, tblSchema, resolution,periods,col=None, startDate=None):
    sql = ""
    if 'd' == resolution: resolution = "DAY"
    if 'm' == resolution: resolution = "MONTH"
    if 'y' == resolution: resolution = "YEAR"

    dDate = " CURDATE() "
    if startDate:
        dDate = (" '%s' " %str(startDate))
    if col:
        sql = "Select DATE ( MIN (%s)) FROM " % str (col)
        if tblSchema:
            sql += tblSchema + "." + tblName
        else:
            sql += tblName
    else:
        sql = "Select DATE ( DATE_ADD(%s, INTERVAL %s %s))" %(dDate,str(periods),str(resolution))
    return sql

def oracle_minValue (tblName, tblSchema, resolution,periods,col=None, startDate=None ):
    sql = ""
    dDate = " getdate() "
    if startDate:
        dDate = (" TO_DATE ('%s') " % str(startDate))
    if col:
        sql = "Select trunc (MIN (%s) ) FROM " % str (col)
        if tblSchema:
            sql += "`"+tblSchema + "`" + "." + "`" + tblName + "`"
        else:
            sql += "`" + tblName + "`"
    if 'd' in resolution:
        sql = 'Select trunc (%s+%s) from dual;' %(dDate, str(periods))
    if 'm' in resolution:
        sql =  'Select trunc (add_months(%s, %s)) from dual;' %(dDate, str(periods))
    if 'y' in resolution:
        sql =  'Select trunc (add_months(%s, %s)) from dual;' %(dDate, str(periods*12))
    return sql

######### SQL : MERGE : dstTable, srcTable, mergeKeys, colList , colFullList
def sql_merge (dstTable, srcTable, mergeKeys, colList , colFullList):
        sql = "MERGE INTO " + dstTable + " as t USING " + srcTable + " as s ON ("
        colOnMerge = " AND ".join(["ISNULL (t." + c + ",'')= ISNULL (s." + c +",'')" for c in mergeKeys])
        sql += colOnMerge + ") \n WHEN MATCHED THEN UPDATE SET \n"
        for c in colList:
            # Merge only is source is not null
            sql += "t." + c + "=" + "case when s." + c + " is null or len(s." + c + ")<1 then t." + c + " else s." + c + " End,\n"
        sql = sql[:-2] + "\n"
        sql += " WHEN NOT MATCHED THEN \n"
        sql += " INSERT (" + ",".join([c for c in colFullList]) + ") \n"
        sql += " VALUES  (" + ",".join(["s." + c for c in colFullList]) + "); "

        return sql


######### SQL : SEQUENCE : column, type, start, leg
def sql_seq (seqDic):
    sql = ""
    if 'column' in seqDic and 'type' in seqDic and 'start' in seqDic and 'inc' in seqDic:
        if 'merge' in seqDic:
            # "["+seqDic['column']+"]"+"\t"+
            sql = "["+seqDic['type']+"],\n"
        else:
            sql = "["+seqDic['type']+"]"+"\t"+" IDENTITY("+str(seqDic['start'])+","+str(seqDic['inc'])+") NOT NULL,\n"
    return sql





