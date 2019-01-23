########################################    FINANCE MAIN LOADING ########################################################
import sys,argparse, time, os
sys.path.append( os.path.join ( os.path.dirname( __file__ ) , "../../../"))
from lib.popeye.config import config
config.CONNECTIONS_ACTIVE   = {"sql": "cnDb", "oracle": "cnDb","file": "cnFile"}

import lib.popeye.mapp.mapper as mapper
import lib.popeye.loader.loader as loader
from repo.gFunc import preLogsInDB, logsToDb, sendSMTPMsg

config.DIR_DATA             =  "C:\\bitBucket\\mapper\\schema\\bnz\\pacs"
# Setting paramters
config.CONN_URL = {
                        'sql'       :   "DRIVER={SQL Server};SERVER=SRV-BI,1433;DATABASE=BZ_PACS;UID=bpmk;PWD=bpmk;",
                        'sqlrepo'   :   "DRIVER={SQL Server};SERVER=SRV-BI,1433;DATABASE=BZ_PACS;UID=bpmk;PWD=bpmk;",
                        'oracle'    :   {'dsn':'mstore','user':'system','pass':'a1d2m7i4','nls':"HEBREW_ISRAEL.IW8MSWIN1255"}     #"DSN=BZP;PWD=manager;charset=utf8"

                    }

# 'oracle':"Driver={Oracle ODBC Driver};Dbq=BZP;UID=OUTLN;PWD=manager"

config.TO_TRUNCATE          = True
#config.FILES_NOT_INCLUDE    = ['fin.json', 'finCsv.json']
config.FILES_NOT_INCLUDE    = ['test.json']
config.QUERY_SORT_BY_SOURCE = False
config.LOGS_COUNT_SRC_DST   = False
config.LOGS_IN_DB           = True
config.SMTP_RECEIVERS = ['Oren.Muslavi@b-zion.org.il']  # 'tal@bpmk.co.il'

config.QUERY_PARAMS = {
}

queryDBType = 'sql'
queryDBConn = config.CONN_URL[queryDBType]
qLocation   = config.DIR_DATA+"\\query\\"

#oneTimeLoading = [(qLocation+"staticData.sql",)]

qs = [
]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Loading data from json files, cant get: source list files or destination list files or append mode () ')
    preLogsInDB ()
    timeTuple = []

    startTime = time.time()
    mapper.loadJson()
    loader.loading()
    loadingTime = time.time()
    timeTuple.append((config.MSG_SEND_TABLE[1], (loadingTime - startTime) / 60))

    #execSP.execQuery(connType=queryDBType, connString=queryDBConn,sqlWithParamList=qs)
    queryTime = time.time()
    timeTuple.append((config.MSG_SEND_TABLE[2], (queryTime - loadingTime) / 60))

    #OLAP_Process(serverName='SRV-BI', dbName='finance', cubes=[], dims=[], fullProcess=True)
    olapTime = time.time()
    timeTuple.append((config.MSG_SEND_TABLE[3], (olapTime - queryTime) / 60))

    logsToDb()
    sendSMTPMsg(timeTuple=timeTuple, jobName="PACS", onlyErr=False)