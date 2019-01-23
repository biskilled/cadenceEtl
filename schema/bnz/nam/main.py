import sys, argparse, time, os, datetime
sys.path.append( os.path.join ( os.path.dirname( __file__ ) , "../../../"))
from lib.popeye.config import config
config.CONNECTIONS_ACTIVE   = {"sql": "cnDb", "oracle": "cnDb"}

import lib.popeye.mapp.mapper as mapper
import lib.popeye.loader.loader as loader
import lib.popeye.loader.loadExecSP as execSP
from repo.gFunc import preLogsInDB, logsToDb, sendSMTPMsg, OLAP_Process

# Setting paramters
config.CONN_URL = {
                        'sql'       :   "DRIVER={SQL Server};SERVER=SRV-BI,1433;DATABASE=BZ_NAM;UID=bpmk;PWD=bpmk;",
                        'sqlrepo'   :   "DRIVER={SQL Server};SERVER=SRV-BI,1433;DATABASE=BZ_NAM;UID=bpmk;PWD=bpmk;",
                        'oracle'    :   {'dsn':'BZP','user':'OUTLN','pass':'manager','nls':"hebrew_israel.we8dec"}      #"DSN=BZP;PWD=manager;charset=utf8"
                    }

# 'oracle':"Driver={Oracle ODBC Driver};Dbq=BZP;UID=OUTLN;PWD=manager"
config.DIR_DATA             =  "C:\\bitBucket\\mapper\\schema\\bnz\\nam"
config.TO_TRUNCATE          = True
#config.FILES_NOT_INCLUDE    = ['test.json']
config.FILES_NOT_INCLUDE    = ['dwh.json','dims.json','test.json']
#config.FILES_NOT_INCLUDE    = ['critical.json','medumTbls.json','smallTbls.json','TN_Y_Tbls.json','dims.json','dwh.json','dims.json']

config.QUERY_SORT_BY_SOURCE = False
config.LOGS_COUNT_SRC_DST   = False
config.LOGS_IN_DB           = True
config.SMTP_RECEIVERS = ['Oren.Muslavi@b-zion.org.il']  # 'tal@bpmk.co.il'

dataRange, curDate = (1,400,"%Y%m%d",) , datetime.datetime.today()
startDay = (curDate - datetime.timedelta(days=dataRange[1])).strftime(dataRange[2])
endDay   = (curDate - datetime.timedelta(days=dataRange[0])).strftime(dataRange[2])

#20100101
config.QUERY_PARAMS = {
    "$start" : startDay,       #startDay, "20100101"
    "$end"   : endDay
}

queryDBType = 'sql'
queryDBConn = config.CONN_URL[queryDBType]
qLocation   = config.DIR_DATA+"\\query\\"

oneTimeLoading = [(qLocation+"staticData.sql",)]

qs = [
    (1, qLocation+"updateNBEW.sql"   ,{}),
    (2, "exec [dbo].[Create_Dim_Cases]"   ,{}),
    (2, "exec [dbo].[Create_DIM_PATIENT_TYPE]"   ,{}),
    (3, "exec create_Fact_Hachnasot"   ,{}),
    (4, "exec [dbo].[Update_Nlei_values] @last_etl_date='20160101'"   ,{'last_etl_date':config.QUERY_PARAMS['$start']}),
    (4, "exec dbo.Create_fact_ishpuz_tables"   ,{}),
    (5, "exec dbo.Create_Hosp_Daily_Status"   ,{}),
    (6, "exec dbo.Set_Infected_Daily"   ,{}),
    (7, "exec dbo.Create_fact_ishpuzim"   ,{}),
    (7, "exec create_CLN_IshpuzimIndicators"   ,{}),
    (7, "exec dbo.Create_Fact_Hayavim"   ,{}),
    (8, "exec Create_Fact_Miun"   ,{}),
    (9, "exec SP_Sterna_Build_Nituach"   ,{})
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

    OLAP_Process(serverName='SRV-BI', dbName='namer', cubes=[], dims=[], fullProcess=True)
    olapTime = time.time()
    timeTuple.append((config.MSG_SEND_TABLE[3], (olapTime - queryTime) / 60))

    logsToDb()
    sendSMTPMsg(timeTuple=timeTuple, jobName="NAMER", onlyErr=False)