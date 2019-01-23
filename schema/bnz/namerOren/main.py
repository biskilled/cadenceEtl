import sys, argparse, time, os, datetime
sys.path.append( os.path.join ( os.path.dirname( __file__ ) , "../../../"))
from lib.popeye.config import config
config.CONNECTIONS_ACTIVE   = {"sql": "cnDb", "oracle": "cnDb"}

import lib.popeye.mapp.mapper as mapper
import lib.popeye.loader.loader as loader
from repo.gFunc import preLogsInDB, logsToDb, sendSMTPMsg

# Setting paramters
config.CONN_URL = {
                        'sql'       :   "DRIVER={SQL Server};SERVER=SRV-BI,1433;DATABASE=BZ_NAM;UID=bpmk;PWD=bpmk;",
                        'sqlrepo'   :   "DRIVER={SQL Server};SERVER=SRV-BI,1433;DATABASE=BZ_NAM;UID=bpmk;PWD=bpmk;",
                        'oracle'    :   {'dsn':'BZP','user':'OUTLN','pass':'manager','nls':"hebrew_israel.we8dec"}      #"DSN=BZP;PWD=manager;charset=utf8"
                    }

# 'oracle':"Driver={Oracle ODBC Driver};Dbq=BZP;UID=OUTLN;PWD=manager"
#config.DIR_DATA             =  "C:\\bitBucket\\mapper\\schema\\bnz\\namerOren"
config.DIR_DATA             =  "C:\\bitBucket\\mapper\\schema\\bnz\\namerOren"
config.TO_TRUNCATE          = True
config.FILES_NOT_INCLUDE    = ['documentLoading.json']

config.QUERY_SORT_BY_SOURCE = False
config.LOGS_COUNT_SRC_DST   = False
config.LOGS_IN_DB           = True
config.SMTP_RECEIVERS = ['Oren.Muslavi@b-zion.org.il']

dataRange, curDate = (1,30,"%Y%m%d",) , datetime.datetime.today()
startDay = (curDate - datetime.timedelta(days=dataRange[1])).strftime(dataRange[2])
endDay   = (curDate - datetime.timedelta(days=dataRange[0])).strftime(dataRange[2])

config.QUERY_PARAMS = {
    "$start" : '20140101',
    "$end"   : endDay
}

config.RESULT_ARRAY_SIZE = 50000
config.LOGS_IN_DB = False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Loading data from json files, cant get: source list files or destination list files or append mode () ')
    timeTuple = []
    preLogsInDB ()

    startTime = time.time()
    mapper.loadJson()
    loader.loading()
    loadingTime = time.time()
    timeTuple.append((config.MSG_SEND_TABLE[1], (loadingTime - startTime) / 60))

    logsToDb()
    sendSMTPMsg(timeTuple=timeTuple, jobName="INTERNAL LOADING NAMER", onlyErr=False)