import time
import logging
import os
import sys
from collections import OrderedDict

#from popEtl.config import config


class ListHandler(logging.Handler):  # Inherit from logging.Handler
    def __init__(self):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Our custom argument
        self.log_list = []

    def emit(self, record):
        # record.message is the log message
        self.log_list.append(self.format(record))

class getLogger (object):
    def __init__ (self, logStdout=True, logDir=None, logFile='log',logErrFile="log",
                  toSendErr=False, loggLevel=logging.DEBUG, logFormat='%(asctime)s %(levelname)s %(message)s'):

        currentDate     = time.strftime('%Y%m%d')
        self.logDir     = logDir
        self.logFormat  = logFormat
        self.logFile    = "%s_%s.log"%(logFile,currentDate)    if logFile and ".log" not in logFile.lower() else logFile
        self.logErrFile = "%s_%s.err"%(logErrFile,currentDate) if logErrFile and ".err" not in logErrFile.lower() else logErrFile
        self.logLevel   = loggLevel
        self.logStdout  = logStdout
        self.toSendErr  = toSendErr
        self.listHandler= None

        #logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        logFormatter= logging.Formatter(self.logFormat)
        self.logg  = logging.getLogger()

        if self.toSendErr:
            self.listHandler = ListHandler()
            self.listHandler.setFormatter(logFormatter)
            self.listHandler.setLevel(logging.ERROR)
            self.logg.addHandler(self.listHandler)

        if self.logDir and self.logFile:
            self._setLogsFiles()

        if self.logStdout:
            consoleHandler = logging.StreamHandler(sys.stdout)
            consoleHandler.setFormatter(logFormatter)
            self.logg.addHandler(consoleHandler)

        self.logg.setLevel( self.logLevel )

    def getLogger (self):
        return self.logg

    def gerListErr (self):
        if self.listHandler:
            return self.listHandler.log_list

    def getLogsDir (self):
        return self.logDir

    def setLogLevel (self, logLevel):
        self.logLevel = logLevel

    def _setLogsFiles(self, logFormatter):

        if not os.path.isdir(self.logDir):
            err = "%s if not a correct directory " % self.logDir
            raise ValueError(err)

        if not self.logErrFile:
            fileHandler = logging.FileHandler(os.path.join(self.logDir, self.logFile))
            fileHandler.setFormatter(logFormatter)
            self.logg.addHandler(fileHandler)
        else:
            # log file info
            fileHandlerInfo = logging.FileHandler(os.path.join(self.logDir, self.logFile), mode='a')
            fileHandlerInfo.setFormatter(logFormatter)
            fileHandlerInfo.setLevel(logging.INFO)
            self.logg.addHandler(fileHandlerInfo)

            # Err file info
            fileHandlerErr = logging.FileHandler(os.path.join(self.logDir, self.logErrFile), mode='a')
            fileHandlerErr.setFormatter(logFormatter)
            fileHandlerErr.setLevel(logging.ERROR)
            self.logg.addHandler(fileHandlerErr)


class manageTime (object):
    class eDic (object):
        desc = "desc"
        ts   = "timestamp"
        tCnt = "totaltime"

    def __init__ (self, loggObj, timeFormat="%m/%d/%Y %H:%M:%S", sDesc="state_",  toSendErrors=True):
        self.startTime= time.time()
        self.stateDic = OrderedDict()
        self.stateCnt = 0
        self.sDesc    = sDesc
        self.loggObj  = loggObj
        self.loggObj.toSendErr = toSendErrors

        #localTime = datetime.datetime.today()
        #timeStr = localTime.strftime(timeFormat)

    def addState (self, sDesc=None):
        self.stateCnt+=1
        if not sDesc:
            sDesc="%s%s" %(str(self.sDesc),str(self.stateCnt))
        ts = time.time()
        tCnt = (ts - self.startTime) / 60
        self.stateDic[self.stateCnt] = {self.eDic.desc:sDesc, self.eDic.ts:ts,self.eDic.tCnt:tCnt }

    def deleteOldLogFiles (self, days=5 ):
        logsDir = self.loggObj.getLogsDir()
        if logsDir:
            now = time.time()
            old = now - (days * 24 * 60 * 60)

            for f in os.listdir(logsDir):
                path = os.path.join(logsDir, f)
                if os.path.isfile(path):
                    stat = os.stat(path)
                    if stat.st_ctime < old:
                        self.loggObj.info("Delete File %s" %(path))

    def sendSMTPmsg (self, msgName, onlyOnErr=False, withErr=True):

        htmlDic = OrderedDict()
        msgSubj =  "Loading JOB %s " %(msgName)

        for t in self.stateDic:
            htmlDic[t[0]] = t[1]


