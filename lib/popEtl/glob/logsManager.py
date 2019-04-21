import time
import logging
import os
import sys
import smtplib
from collections import OrderedDict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from popEtl.glob.genHtml import eHtml, createHtmlFromList
from popEtl.config import config

class ListHandler(logging.Handler):  # Inherit from logging.Handler
    def __init__(self):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Our custom argument
        self.log_list = []

    def emit(self, record):
        # record.message is the log message
        self.log_list.append(self.format(record))

    def getList (self):
        return self.log_list

class myLogger (object):
    def __init__ (self, logStdout=True, loggLevel=logging.DEBUG, logFormat='%(asctime)s %(levelname)s %(message)s'):
        # logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        self.logFormatter   = logging.Formatter(logFormat)
        self.logLevel       = loggLevel
        self.isLogsFilesInit= False
        self.logTmpFile     = None

        self.logg           = logging.getLogger()
        self.logg.setLevel(self.logLevel)

        if logStdout:
            consoleHandler = logging.StreamHandler(sys.stdout)
            consoleHandler.setFormatter(self.logFormatter)
            self.logg.addHandler(consoleHandler)

    def setLogsFiles (self, logDir=None, logFile='log',
                      logErrFile="log",logTmpFile='lastLog'):

        self.logDir = logDir if logDir else config.LOGS_DIR
        currentDate = time.strftime('%Y%m%d')
        logFile = logFile if logFile else config.LOGS_INFO_NAME
        logFile = "%s_%s.log"%(logFile, currentDate) if logFile and ".log" not in logFile.lower() else logFile

        logErrFile = logErrFile if logErrFile else config.LOGS_ERR_NAME
        logErrFile = "%s_%s.err" % (logErrFile, currentDate) if logErrFile and ".err" not in logErrFile.lower() else logErrFile

        logTmpFile = logTmpFile if logTmpFile else config.LOGS_TMP_NAME
        logTmpFile = "%s.err" % (logTmpFile) if logTmpFile and ".err" not in logTmpFile.lower() else logTmpFile

        if not os.path.isdir(self.logDir):
            err = "%s if not a correct directory " % self.logDir
            raise ValueError(err)

        if logTmpFile:
            self.logTmpFile = os.path.join(self.logDir, logTmpFile)
            tmpFileErrors   = logging.FileHandler(self.logTmpFile, mode='a')
            tmpFileErrors.setFormatter(self.logFormatter)
            tmpFileErrors.setLevel(logging.ERROR)
            self.logg.addHandler(tmpFileErrors)

        if not logErrFile:
            fileHandler = logging.FileHandler(os.path.join(self.logDir, logFile), mode='a')
            fileHandler.setFormatter(self.logFormatter)
            self.logg.addHandler(fileHandler)
        else:
            # log file info
            fileHandlerInfo = logging.FileHandler(os.path.join(self.logDir, logFile), mode='a')
            fileHandlerInfo.setFormatter(self.logFormatter)
            fileHandlerInfo.setLevel(self.logLevel)
            self.logg.addHandler(fileHandlerInfo)

            # Err file info
            fileHandlerErr = logging.FileHandler(os.path.join(self.logDir, logErrFile), mode='a')
            fileHandlerErr.setFormatter(self.logFormatter)
            fileHandlerErr.setLevel(logging.ERROR)
            self.logg.addHandler(fileHandlerErr)

    def getLogger (self):
        return self.logg

    def getLogsDir (self):
        return self.logDir

    def setLogLevel (self, logLevel):
        self.logLevel = logLevel
        self.logg.setLevel(self.logLevel)

    def setLogDir (self, logDir, logFile='log',logErrFile="log",logTmpFile='lastLog'):
        if os.path.isdir(logDir):
            self.logDir = logDir
            self.setLogsFiles (logDir=logDir, logFile=logFile,
                      logErrFile=logErrFile,logTmpFile=logTmpFile)
        else:
            err = "Logs dir: %s NOT VALID !" %(logDir)
            raise ValueError(err)

    def getLogTemp (self):
        lines = None
        if self.logDir and self.logTmpFile:
            fileLoc = os.path.join (self.logDir,self.logTmpFile)
            if fileLoc and os.path.isfile(fileLoc):
                with open (fileLoc) as f:
                    lines = f.read().splitlines()
        return lines

class manageTime (object):
    class eDic (object):
        desc = "desc"
        ts   = "timestamp"
        tCntLast = "totalFromLastStep"
        tCnt = "totaltime"

    def __init__ (self, loggObj, timeFormat="%m/%d/%Y %H:%M:%S", sDesc="state_" ):
        self.startTime = time.time()
        self.lastTime  = self.startTime
        self.stateDic = OrderedDict()
        self.loggObj  = loggObj
        self.logg  = self.loggObj.getLogger()
        self.timeFormat = timeFormat
        self.stateCnt = 0
        self.sDesc    = sDesc

    def start (self,desc=None,days=None):
        self.startTime = time.time()
        self.lastTime = self.startTime
        if desc:
            self.addState(sDesc=desc)
        if days:
            self.deleteOldLogFiles(days=days)

    def addState (self, sDesc=None):
        self.stateCnt+=1
        if not sDesc:
            sDesc="%s%s" %(str(self.sDesc),str(self.stateCnt))
        ts = time.time()
        tsStr = time.strftime(self.timeFormat, time.localtime(ts))
        tCntFromStart = str(round ( ((ts - self.startTime) / 60) , 2))
        tCntFromLaststep = str(round ( ((ts - self.lastTime) / 60) , 2))
        self.lastTime = ts
        self.stateDic[self.stateCnt] = {self.eDic.desc:sDesc,
                                        self.eDic.ts:tsStr,
                                        self.eDic.tCntLast:tCntFromLaststep,
                                        self.eDic.tCnt:tCntFromStart }

    def deleteOldLogFiles (self, days=5 ):
        logsDir = self.loggObj.getLogsDir()
        if logsDir:
            now = time.time()
            old = now - (days * 24 * 60 * 60)
            for f in os.listdir(logsDir):
                path = os.path.join(logsDir, f)
                if os.path.isfile(path):
                    stat = os.stat(path)
                    if stat.st_mtime < old:
                        self.logg.info("Delete File %s" %(path))
                        os.remove(path)

    def sendSMTPmsg (self, msgName, onlyOnErr=False, withErr=True):
        okMsg = "Loading JOB %s " %(msgName)
        errMsg= "ERROR loading Job %s " %(msgName)
        endMsg= "Total Execution job "
        errList = self.loggObj.getLogTemp ()
        errCnt  = len(errList) if errList else 0

        htmlList = []
        msgSubj = okMsg if errCnt<1 else errMsg

        if onlyOnErr and errCnt>0 or not onlyOnErr:
            # First table - general knowledge
            self.addState(sDesc=endMsg)

            dicFirstTable = {eHtml.HEADER:['Step Num','Start Time','Desc','Exec Time', 'Total Time'],
                             eHtml.ROWS:[]}

            for st in self.stateDic:
                dicFirstTable[eHtml.ROWS].append ( [st, self.stateDic[st][self.eDic.ts],
                                                    self.stateDic[st][self.eDic.desc],
                                                    self.stateDic[st][self.eDic.tCntLast],
                                                    self.stateDic[st][self.eDic.tCnt] ] )

            htmlList.append (dicFirstTable)
            if withErr:
                # 2nd table - errors tables
                dicFirstTable = {eHtml.HEADER: ['Error Desc'],
                                 eHtml.ROWS: []}
                for err in errList:
                    dicFirstTable[eHtml.ROWS].append ( [err] )

                htmlList.append(dicFirstTable)

            msgHtml = createHtmlFromList(htmlList=htmlList, htmlHeader=msgName)
            self.__sendSMTP(msgSubj=msgSubj, msgHtml=msgHtml)

    def __sendSMTP (self, msgSubj, msgHtml=None, msgText=None):
        sender          = config.SMTP_SENDER
        receivers       = ", ".join(config.SMTP_RECEIVERS)
        receiversList   = config.SMTP_RECEIVERS
        serverSMTP      = config.SMTP_SERVER
        serverUsr       = config.SMTP_SERVER_USER
        serverPass      = config.SMTP_SERVER_PASS

        msg = MIMEMultipart('alternative')
        msg['Subject']  = msgSubj
        msg['From']     = sender
        msg['To']       = receivers

        if msgText:
            textInMail = ''
            if isinstance(msgText, list):
                for l in msgText:
                    textInMail += l + "\n"
            else:
                textInMail = msgText

            msg.attach(MIMEText(textInMail, 'plain'))

        if msgHtml and len(msgHtml)>0:
            msg.attach( MIMEText(msgHtml, 'html') )

        try:
            server = smtplib.SMTP(serverSMTP)
            server.ehlo()
            server.starttls()

            server.login(serverUsr, serverPass)
            server.sendmail(sender, receiversList, msg.as_string())
            server.quit()
        except smtplib.SMTPException:
            err = "gFunc->sendMsg: unable to send email to %s, subject is: %s " % (str(receivers), str(msgSubj))
            raise ValueError(err)

logger = myLogger(logStdout=True,loggLevel=config.LOGS_DEBUG)