|PyPI version| |Docs badge| |Build Status| |License|

**********
popEye-Etl
**********

popEye-Etl is build for quick design and implement small or large, simple or complex 
data integration projects. We aim to build a simple way that will enable to answer quickly on
what do we need and how do we do it. 

Documnation is in progress and will be found under http://www.biSkilled.com 

installtion:
Download as zip file all project content or use pip install (in-progress)

Roadmap
=======

Currently popEye-Etl support Sql server, Access, vertica, my-sql, oracle, mongo
In the near future we will add salesforce API support.
Our goals in this project: 
    - extend our connectors liberary add as many connectors as we can
        SalesForce APIs are already coocked ....
    - Add functionalty to manage businees-logic - 
        - Enable Sql script to use python code 
        - Add transfomation functionalties 
        - Add analytics functionalties using sikit-learn / keras / pyToarch    
    
     


# MAPPER #
    - mapping and loading source to target and multiprocess loading
      Supporting : file, sqlserver, mysql, oracle, vertica, access ['access','Driver','FolderPth']
      access - ['access','Driver','FolderPth']. will use json file name as Db name
    
    - loading json configuration and mapp or load.
        source, target, columns, mapping, query, partition, merge

    - requirement modules :
        sqlparse
        ceODBC
        pyodbc
        
     - stt/ sttappend option : t(type), s(source), f(function), c(calculation field based on fiew target columns)
        
# CONFIG #
    QUERY_SORT_BY_SOURCE -> TRUE will sort mappoing by sort definistion (if column exists twice - will be sorted by that else       
                            mapping will be as it is (first all column from source ant then new colmns) 
# Main methods: #
1.  mapper.loadJson(sourceList=None, destList=None)
    If there is a source or destination list will load only listed objects 
    Based on json files configuration
    available Json configuration:
                'target' / 'tar'            -> [ objType, objName ]     Map target 
                'source' / 'src'            -> [ objType, objName ]     Map source
                'query'                     -> [ objType, query statement ] map SOURCE query (if there is source and query -will use query only)
                'columns','column','col'    -> {'column_name':'column type' ... } Only for target object with data types 
                'mapping', 'map'            -> {'target name':'source name'} convert names to target table
                'stt' / 'sttappend'         -> {'target name':"s":source name, "t":column type, "f":"[list of functions]""}
                                                function only for loading, another way to map source to target or update column type

2.  loader.loading(appendData=False, sourceList=None, destList=None)
    If there is a source or destination list will load only listed objects
    Append (no truncate) or truncate->insert, list of sourceses to load or list of destination to load
        available Json configuration:
        'target' / 'tar'            -> [ objType, objName, [ where close] ]     Map target
        'source' / 'src'            -> [ objType, objName, [where clouse] ]     Map source
        'query'                     -> [ objType, query statement ] map SOURCE query (if there is source and query -will use source only)
        'mapping', 'map'            -> {'source name':'target name'} Will load source column to destination by using mapping
        'partition                  -> {"column":<column_name>, "agg":<d,m,y>,"start":<-leg number>} --> 
                                        Based on date time column. if start=None  will load all data. availabe partition are: d=day, m=month, y=year
        'merge'                     -> [ tblName, keyList ] will merge with target table (based on target connection string)
                                        KeyList - list of fields to join merge and target tables
        'inc' / 'Incremental'       -> ['column',start]
                                        will load data from location stored in sqlLite\
                                        Todo: Think if this is optimal, update last from target table as well                                        
        'seq'                       -> ['column', start=1, seq=1, type=INT ]
        
    

3. config - main configuration table
    DIR_DATA        --> Folder with all json files to load
    CONN_TYPES      --> all connection for all used objTypes


5. loaderExecSp.execQuery (connType, connString ,sqlWithParamList)
    connType    -> which DB type to use
    connString  -> connection String to DB
    sqlWithParamList -> can send 1,2 or 3 paramters
        if one -> only file/folder location
        if two -> file/folder location , dictionary of parameter to update query {'paramName': paramaValue}
        if tree-> prioriy for multiprocess exectuting (bigger than 0), file/folder location , dictionary of parameter to update query {'paramName': paramaValue}
    


# INTERNAL METHOS # 
1. mapper.py -> Mapping source to target 
   Methods :
         loadJson (sourceList, destList)     --> load all json files in config files, if threr is source will load just listed source, same for destination
         loop on all json configuration files and execute mapper methos
         Available json values:
            'target' / 'tar'            -> Map target [ objType, objName ]
            'source' / 'src'            -> Map source [ objType, objName ] 
            'query'                     -> can only be source, if there is source and query -will use source only
            'columns','column','col'    -> Only for target object - Will create column and data type 
            'mapping', 'map'            -> mapping between source and target columns 
        
         mapper (dicParamters)               -> dicParamters contain all current setting from json files  
            if target, columns              -> will check if table exists and same srtcuture, if not - create new one (old will be renamed with date prefix)
            if no column and **source**        
                1. convert source column data type into destination data type
                2. if there is mapping as well -> will create only mapped column with updated data type
             
         sourceToTargetDataTypes (srcType, trgType, srcColumns)  --> source object type, destination object type and source column list
                internal function for converting source to destination data type
                

2. loader.py -> Loading data from source to target, based on json scripts (file, sqlServer, oracle, mySql) 
        appendPartitions
            creating new selects with approptiate where clouse
        
        execLoading ( (jMap, src, dst, mapping, appendData,ColumnType, isSQL ) )
            this function is the one that do the actual load
            it truncate - truncate target object
            if mapping  - load only mapped column
            if columnType -> will convert date column type to appropiate date
                 
    ###toFinish : ### 
        - check mode mode -
            truncate
            append
            add merge option
            code review 
        
        

3. loadExecSP.py -> Executing business logic from list of proceures to load (file list ,or folder list).  this methods is valid for DB only 
    
    Methods:
    execQuery(connType=connType, connString=connString,sqlWithParamList=scriptPath)
        - connecting to appropaite DB
        - sqlWithParamList - list of tuple that can be with 1,2 or 3 element
            1 elemnt    -> file name                                            : ( <full path of folder or file to procedure> )
            2 element   -> procedure name and paramter dictionay                : ( <full path of folder or file to procedure> , dictionary:{'param name': parama value .... } )
            3 element   -> priority , procedure name and paramter dictionay     : ( priority, <full path of folder or file to procedure> , dictionary:{'param name': parama value .... } )
                prioiry is the the order which the procedures will execute:  #-1 - highset priority#, 1 ... n (n is the lowest prioriy) 
                queries with same priority will execute in parrallel (if no priority - will excecute in parrallel) 
        
        this methos is creating a dictionay - key: priority number, value: tuple of list of files to execute and paramter dictionary
        sample:     {prioriy Number : ( [list of files to execute] , {dictionary of paramters} )  } and execute execSqlSP (prioriy )
                    [ (<folder or file full path>,<dicionary of paramters to update: 'paramater name':paramter value>)]
        
        for each key - execute __execParallel  (priority number , tuple as above, connType, connString)
    
    ##Internal methos:##
    
    __execParallel (priority, ListOftupleFiles, connType, connString)
        this method call __execSql in a single process or multiprocess method
        - if priority is -1 (less than 0) or there is only one file to execute  -> exec in single process
        - if prioriy > 0 and ther are more than 1 file                          -> exec in multi process
    
    __execSql ( (sqlScript, locParams, connType, connString) )
        this method is used for openning script file and replace paramter by using __replaceParameters method.
        if script file contain more than one query (spliteed with GO) - will execute each query sapparted 
        if sciprt contain 'print' - will print massage
        
    __replaceParameters (line, dicParam)
        if there is paramters which are in dicParam and mattching replace matching (from config file) - it will replace by matching pattern
         
         
         
### What is this repository for? ###

* Quick summary
* Version
* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)


