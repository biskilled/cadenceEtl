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
    def __init__ (self, logStdout=True, logDir=None, logFile='log',logErrFile="log",
                  loggLevel=logging.DEBUG, logFormat='%(asctime)s %(levelname)s %(message)s'):

        currentDate     = time.strftime('%Y%m%d')
        self.logDir     = logDir
        self.logFile    = "%s_%s.log"%(logFile,currentDate)    if logFile and ".log" not in logFile.lower() else logFile
        self.logErrFile = "%s_%s.err"%(logErrFile,currentDate) if logErrFile and ".err" not in logErrFile.lower() else logErrFile

        self.logLevel   = loggLevel
        self.logStdout  = logStdout
        self.isLogsFilesInit = False

        #logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        self.logFormatter= logging.Formatter(logFormat)
        self.logg   = logging.getLogger()

        # tmp errors logs into currentLogFile

        self.listH = ListHandler()
        self.listH.setFormatter(self.logFormatter)
        self.listH.setLevel(logging.ERROR)
        self.logg.addHandler(self.listH)

        if self.logDir and self.logFile and not self.isLogsFilesInit:
            self.isLogsFilesInit = True
            self.__setLogsFiles()

        if self.logStdout:
            consoleHandler = logging.StreamHandler(sys.stdout)
            consoleHandler.setFormatter(self.logFormatter)
            self.logg.addHandler(consoleHandler)

        self.logg.setLevel( self.logLevel )

    def getLogger (self):
        return self.logg

    def gerListErr (self):
        if self.listH:
            return self.listH.log_list

    def getLogsDir (self):
        return self.logDir

    def setLogLevel (self, logLevel):
        self.logLevel = logLevel
        if not self.isLogsFilesInit:
            self.isLogsFilesInit = True
            self.__setLogsFiles()

    def setLogDir (self, logDir):
        if os.path.isdir(logDir):
            self.logDir = logDir

        else:
            err = "Logs dir: %s NOT VALID !" %(logDir)
            raise ValueError(err)

    def __setLogsFiles(self):
        if not os.path.isdir(self.logDir):
            err = "%s if not a correct directory " % self.logDir
            raise ValueError(err)

        if not self.logErrFile:
            fileHandler = logging.FileHandler(os.path.join(self.logDir, self.logFile))
            fileHandler.setFormatter(self.logFormatter)
            self.logg.addHandler(fileHandler)
        else:
            # log file info
            fileHandlerInfo = logging.FileHandler(os.path.join(self.logDir, self.logFile), mode='a')
            fileHandlerInfo.setFormatter(self.logFormatter)
            fileHandlerInfo.setLevel(self.logLevel)
            self.logg.addHandler(fileHandlerInfo)

            # Err file info
            fileHandlerErr = logging.FileHandler(os.path.join(self.logDir, self.logErrFile), mode='a')
            fileHandlerErr.setFormatter(self.logFormatter)
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
        self.timeFormat = timeFormat

    def addState (self, sDesc=None):
        self.stateCnt+=1
        if not sDesc:
            sDesc="%s%s" %(str(self.sDesc),str(self.stateCnt))
        ts = time.time()
        tsStr = time.strftime(self.timeFormat, time.localtime(ts))
        tCnt = str(round ( ((ts - self.startTime) / 60) , 2))
        self.stateDic[self.stateCnt] = {self.eDic.desc:sDesc, self.eDic.ts:tsStr,self.eDic.tCnt:tCnt }

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
        okMsg = "Loading JOB %s " %(msgName)
        errMsg= "ERROR loading Job %s " %(msgName)
        endMsg= "Total Execution job "
        errList = self.loggObj.gerListErr ()
        errCnt  = len(errList) if errList else 0

        htmlList = []
        msgSubj = okMsg if errCnt<1 else errMsg

        if onlyOnErr and errCnt>0 or not onlyOnErr:
            # First table - general knowledge
            self.addState(sDesc=endMsg)

            dicFirstTable = {eHtml.HEADER:['Step Num','Start Time','Desc','Total Time'],
                             eHtml.ROWS:[]}

            for st in self.stateDic:
                dicFirstTable[eHtml.ROWS].append ( [st, self.stateDic[st][self.eDic.ts], self.stateDic[st][self.eDic.desc], self.stateDic[st][self.eDic.tCnt] ] )

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

logger = myLogger(logStdout=True, logDir=config.LOGS_DIR, logFile=config.LOGS_INFO_NAME,
                   logErrFile=config.LOGS_ERR_NAME,loggLevel=config.LOGS_DEBUG)