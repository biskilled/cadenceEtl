import time

from popEtl.config import config
from popEtl.connections.connector import connector

class manageTime (object):
    class eDic (object):
        desc = "desc"
        ts   = "timestamp"
        tCnt = "totaltime"

    def __init__ (self, timeFormat="%m/%d/%Y %H:%M:%S", sDesc="state_"):
        self.startTime= time.time()
        self.stateDic = OrderedDict()
        self.stateCnt = 0
        self.sDesc    = sDesc
        #localTime = datetime.datetime.today()
        #timeStr = localTime.strftime(timeFormat)

    def addState (self, sDesc=None):
        self.stateCnt+=1
        if not sDesc:
            sDesc="%s%s" %(str(self.sDesc),str(self.stateCnt))
        ts = time.time()
        tCnt = (ts - self.startTime) / 60
        self.stateDic[self.stateCnt] = {self.eDic.desc:sDesc, self.eDic.ts:ts,self.eDic.tCnt:tCnt }

    def _isRepoExists (self):
        logObj = None
        for connType in config.CONN_URL:
            if "repo" in connType.lower():
                connUrl = config.CONN_URL[connType]
                connType = connType.lower().replace("repo", "")
                logObj = connector(connType=connType, connJsonVal=connUrl)
                break
        return logObj

    def cleanLogsDB (self ):
        querySteps = []
        logObj = self._isRepoExists()
        if logObj:
            for tbl in config.LOGS_DB_TBL:
                sql = "Delete from " + tbl + " where " + config.LOGS_DB_TBL[tbl]["d"] + "<dateadd(d,-" + str(
                    config.LOGS_DB_TBL[tbl]["days"]) + ",getdate());"
                querySteps.append([sql])


            sql2 = """
                Delete from [""" + config.LOGS_TBL_COUNT + """"] where not exists
                (Select 1 from
                    (Select intDate, tbl From
                        (Select RANK() OVER (Partition by tblDest order by uDate) rnk, uDate as intDate, tblTest as tbl from [""" + config.LOGS_TBL_COUNT + """"]
                         UNION
                         Select RANK() OVER (Partition by tblDest order by uDate desc) rnk, uDate as intDate, tblTest as tbl from [""" + config.LOGS_TBL_COUNT + """"] ) aa
                     Where aa.rnk=1 ) bb
                Where bb.intDate = uDate and bb.tbl=tblDest )
            """

            for connType in config.CONN_URL:
                if "repo" in connType.lower():
                    connUrl = config.CONN_URL[connType]
                    connType = connType.lower()
                    connType = connType.replace("repo", "")
                    isRepoTblsExists = True
                    break

            if isRepoTblsExists:
                execQuery(connType=connType, connString=connUrl, sqlWithParamList=querySteps)
            p("gFunc->preLogsInDB: DB Config is ON, exec queries: %s" % (str(querySteps)), "ii")
        else:
            p("gFunc->preLogsInDB: DB Config is OFF, do nothing  .... ", "ii")


