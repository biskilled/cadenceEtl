########################################    FINANCE MAIN LOADING ########################################################
import sys,argparse, time,os

sys.path.append( os.path.join ( os.path.dirname( __file__ ) , "../../../"))
from lib.popeye.config import config
config.CONNECTIONS_ACTIVE   = {"sql": "cnDb", "file": "cnFile"}

import lib.popeye.mapp.mapper as mapper
import lib.popeye.loader.loader as loader
import lib.popeye.loader.loadExecSP as execSP
from repo.gFunc import preLogsInDB, logsToDb, sendSMTPMsg,OLAP_Process
# \\zion-cache\talafs\AFSSNH.TXT
# Setting paramters
config.CONN_URL = {
                        'sql'       :   "DRIVER={SQL Server};SERVER=SRV-BI,1433;DATABASE=BZ_EXP;UID=bpmk;PWD=bpmk;",
                        'sqlrepo'   :   "DRIVER={SQL Server};SERVER=SRV-BI,1433;DATABASE=BZ_EXP;UID=bpmk;PWD=bpmk;",
                        'file'      :   {'delimiter':'|','header':False, 'folder':"\\\\zion-cache\\talafs\\", 'encoding':'windows-1255', 'errors':'ignore'}      #"DSN=BZP;PWD=manager;charset=utf8"
                    }

# 'oracle':"Driver={Oracle ODBC Driver};Dbq=BZP;UID=OUTLN;PWD=manager"
config.DIR_DATA             =  "C:\\bitBucket\\mapper\\schema\\bnz\\afs"
config.TO_TRUNCATE          = True
config.FILES_NOT_INCLUDE    = ['afs_Full.json']
#config.FILES_NOT_INCLUDE    = ['test.json', 'dwh.json','smallTbls.json','medumTbls.json','TN_Y_Tbls.json','dims.json']
config.QUERY_SORT_BY_SOURCE = False
config.LOGS_COUNT_SRC_DST   = False
config.LOGS_IN_DB           = True
config.SMTP_RECEIVERS = ['Oren.Muslavi@b-zion.org.il','tal@bpmk.co.il']  # 'tal@bpmk.co.il'

#dataRange, curDate = (1,400,"%Y%m%d",) , datetime.datetime.today()
#startDay = (curDate - datetime.timedelta(days=dataRange[1])).strftime(dataRange[2])
#endDay   = (curDate - datetime.timedelta(days=dataRange[0])).strftime(dataRange[2])

config.QUERY_PARAMS = {
}

queryDBType = 'sql'
queryDBConn = config.CONN_URL[queryDBType]
qLocation   = config.DIR_DATA+"\\query\\"

qs = [
    (1, "exec dbo.SP_STG_Maam"   ,{}),
    (1, "exec dbo.SP_Build_STG_AFS"   ,{}),
    (1, "exec dbo.SP_Build_STG_Hazmanot", {}),
    (2, "exec dbo.SP_Build_STG_Pritim", {}),
    (2, "exec dbo.SP_Build_DIMS_Sapakim_Irgun_Sug_Tnua", {}),
    (2, "exec dbo.SP_BUILD_DWH_DIM_DATES", {}),
    (2, "exec SP_Build_DIM_Machsan_Teuda", {}),
    (3, "exec SP_Trans_Code_NAMER_Full", {}),
    (4, "exec dbo.SP_InsertBudjetPrecents_AFS_Haamasot_Main", {}),
    (4, "exec dbo.SP_InsertBudjetPrecents_AFS_Haamasot_Main2", {}),
    (5, "exec SP_UpdateLoadingExpensesFromFinance", {})

]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Loading data from json files, cant get: source list files or destination list files or append mode () ')
    timeTuple = []
    preLogsInDB ()

    startTime = time.time()
    mapper.loadJson()
    loader.loading()
    loadingTime = time.time()
    timeTuple.append((config.MSG_SEND_TABLE[1], (loadingTime - startTime) / 60))

    execSP.execQuery(connType=queryDBType, connString=queryDBConn,sqlWithParamList=qs)
    queryTime = time.time()
    timeTuple.append((config.MSG_SEND_TABLE[2], (queryTime - loadingTime) / 60))

    OLAP_Process(serverName='SRV-BI', dbName='logistics', cubes=[], dims=[], fullProcess=True)
    olapTime = time.time()
    timeTuple.append((config.MSG_SEND_TABLE[3], (olapTime - queryTime) / 60))

    logsToDb()
    sendSMTPMsg(timeTuple=timeTuple, jobName="LOGISTICS", onlyErr=True )