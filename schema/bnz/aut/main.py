import sys, time,os
sys.path.append( os.path.join ( os.path.dirname( __file__ ) , "../../../"))
from lib.popeye.config import config
config.CONNECTIONS_ACTIVE   = {"sql": "cnDb","sql1": "cnDb", "file": "cnFile"}
import lib.popeye.loader.loader as loader
from repo.gFunc import preLogsInDB, logsToDb, sendSMTPMsg, OLAP_Process

# Setting paramters
config.CONN_URL   = {
                        'sql'   :"DRIVER={SQL Server};SERVER=SRV-BI,1433;DATABASE=BZ_AUT;UID=bpmk;PWD=bpmk;",
                        'sql1'  :"DRIVER={SQL Server};SERVER=MAX2005\MAX2005;DATABASE=BZion-Prod;UID=bztest;PWD=bztest;",
                        'file'  :{'delimiter':'~','header':True, 'folder':"C:\\bi\\data\\automation"}
                     }
# 'sql'   :"DRIVER={SQL Server};SERVER=SRV-BI,1433;DATABASE=DW_AUT;UID=bpmk;PWD=bpmk;",
# 'sql'   :"DRIVER={SQL Server};SERVER=LENOVO-TALS,1433;DATABASE=test;UID=tals;PWD=tals;",
#config.DIR_DATA     =  "C:\\bitBucket\\mapper\\schema\\bnz\\aut"
config.DIR_DATA     =  "C:\\bitBucket\\mapper\\schema\\bnz\\aut"
#config.FILES_NOT_INCLUDE    = ['aut_Max2005.json','autFiles1.json',  'tests.json']
#config.FILES_NOT_INCLUDE    = ['aut_Max2005.json']
config.LOGS_COUNT_SRC_DST   = False
config.LOGS_IN_DB           = True
config.SMTP_RECEIVERS = ['Oren.Muslavi@b-zion.org.il']  # 'tal@bpmk.co.il'

queryDBType = 'sql'
queryDBConn = config.CONN_URL[queryDBType]
qLocation   = config.DIR_DATA+"\\query\\"

querySteps = [
    (1, "exec [dbo].[Loading_Sachar_STG_Data]"   ,{}),
    #(1, qLocation+"stg_fact_payments3.sql"   ,{}),
    #(2, qLocation+"dwh_fact_payments3.sql"   ,{}),
    (2, "exec [dbo].[Loading_DWH_Tables]"   ,{}),
    #(3, qLocation+"dim_departments.sql"   ,{}),
    (3, "exec [dbo].[Loading_DIM_Departments]", {}),
    #(3, qLocation+"dim_employees.sql"   ,{}),
    (3, "exec [dbo].[Loading_Dim_Employee]", {}),
    #(3, qLocation+"dim_semel.sql"   ,{}),
    (3, "exec [dbo].[SP_STG_DIM_SEMEL]", {}),
    #(3, qLocation+"trans_code_full.sql"   ,{}),
    (3, "exec [dbo].[SP_Trans_Code_AUT_Full]", {}),
    #(3, qLocation +"dim_y_irgunit.sql", {}),
    (3, "exec [dbo].[SP_DWH_DIM_Y_IRGUNIT]", {}),
    #(4, qLocation+"dim_employee_full.sql"   ,{})
    (4, "exec [dbo].[SP_Build_STG_DIM_Employee_Full]", {})
]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Loading data from json files, cant get: source list files or destination list files or append mode () ')
    timeTuple = []
    preLogsInDB()
    startTime = time.time()
    #mapper.loadJson()
    loader.loading()
    loadingTime = time.time()
    timeTuple.append( (config.MSG_SEND_TABLE[1], (loadingTime - startTime) / 60 ) )

    #execSP.execQuery(connType=queryDBType, connString=queryDBConn,sqlWithParamList=querySteps)
    queryTime = time.time()
    timeTuple.append((config.MSG_SEND_TABLE[2], (queryTime - loadingTime) / 60))

    OLAP_Process(serverName='SRV-BI', dbName='aut', cubes=[], dims=[], fullProcess=True)
    olapTime = time.time()
    timeTuple.append((config.MSG_SEND_TABLE[3], (olapTime - queryTime)  / 60))

    logsToDb()
    sendSMTPMsg(timeTuple=timeTuple, jobName="AUTOMATION", onlyErr = True)