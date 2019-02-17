# (c) 2017-2019, Tal Shany <tal.shany@biSkilled.com>
#
# This file is part of popEye
#
# popEye is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# popEye is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cadenceEtl.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import  (absolute_import, division, print_function)
__metaclass__ = type


import smtplib
import re
import sys

from config import config
from glob.glob import p
from loader.loadExecSP import execQuery
from connections.db import cnDb

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def checkSequence(seqProp):
    ret = {}
    if (isinstance(seqProp, dict)):
        if 'column' in seqProp:
            ret['column'] = seqProp['column']
        else:
            p("Sequence is exists, but not configure properly, add column for suqunce dictionary, seq: %s" % (
            str(seqProp)), "e")
            return None
        ret['type'] = seqProp['type'] if 'type' in seqProp else config.SEQ_DEFAULT_DATA_TYPE
        ret['start'] = str(seqProp['start']) if 'start' in seqProp else str(config.SEQ_DEFAULT_SEQ_START)
        ret['inc'] = str(seqProp['inc']) if 'inc' in seqProp else str(config.SEQ_DEFAULT_SEQ_INC)
        return ret
    else:
        p("Sequence is exists, but not configure properly, add column for suqunce dictionary, seq: %s" % (
        str(seqProp)), "e")
        return None

def sendMsg(subj,text=None, mHTML=None):
    p("gFunc->sendMsg: Start to send mail. text: %s , html: %s , subject: %s " % (str(text), str(mHTML), str(subj)), "ii")
    sender          = config.SMTP_SENDER
    receivers       = ", ".join(config.SMTP_RECEIVERS)
    receiversList   = config.SMTP_RECEIVERS

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subj
    msg['From'] = sender
    msg['To'] = receivers


    textInMail = ''
    html = None

    if text:
        if isinstance(text , list):
            for l in text:
                textInMail += l +"\n"
        else:
            textInMail = text

        msg.attach( MIMEText(textInMail, 'plain') )

    if mHTML and isinstance(mHTML, dict):
        html = """
        <html>
          <head></head>
          <body>
            <table> 
          """
        for m in mHTML:
            html += "<tr>"
            html+= "<td>"+str(m)+"</td>"+"<td>"+str(mHTML[m])+"</td>"
            html += "</tr>"
        html += """
            </table>
          </body>
        </html>        
        """

        msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP(config.SMTP_SERVER)
        server.ehlo()
        server.starttls()

        server.login(config.SMTP_SERVER_USER, config.SMTP_SERVER_PASS)
        server.sendmail(sender, receiversList, msg.as_string())
        server.quit()
        # smtpObj = smtplib.SMTP('smtp.bpmk.co.il',587)
        # smtpObj.sendmail(sender, receivers, message)
        p("gFunc->sendMsg: Successfully sent email to %s , subject is: %s" % (str(receivers), str(subj)), "i")
    except smtplib.SMTPException:
        p("gFunc->sendMsg: unable to send email to %s, subject is: %s " % (str(receivers), str(subj)), "e")

        # sendMsg()

def sendSMTPMsg(timeTuple,jobName, onlyErr = True):

    if (onlyErr and len (config.LOGS_ARR_E)>0) or not onlyErr:

        subj = config.MSG_SEND_TABLE["subj"] %str(jobName)
        htmlDic = OrderedDict()
        for t in timeTuple:
            htmlDic[t[0]] = t[1]

        if len (config.LOGS_ARR_E)>0:
            subj = config.MSG_SEND_TABLE["subjERR"] %str(jobName)
            errorStr = ''
            for r in config.LOGS_ARR_E:
                if len(r) == 4:
                    htmlRow = str(r[0]) + ":" + str(r[3]) + "<br>"
                    errorStr += htmlRow
            htmlDic[ config.MSG_SEND_TABLE["err"] ] = errorStr
        else:
            subj = config.MSG_SEND_TABLE["subj"] %str(jobName)

        infoStr = ''
        for r in config.LOGS_ARR_I:
            if len(r)==4:
                htmlRow = str(r[0])+":"+str(r[3])+"<br>"
                infoStr += htmlRow
        htmlDic[ config.MSG_SEND_TABLE["inf"] ] = infoStr

        sendMsg(subj, text=None, mHTML=htmlDic)

def preLogsInDB ():
    querySteps = []
    connType   = None
    connUrl    = None
    isRepoTblsExists = False
    if config.LOGS_IN_DB:
        for tbl in config.LOGS_DB_TBL:
            sql = "Delete from " + tbl + " where " + config.LOGS_DB_TBL[tbl]["d"] + "<dateadd(d,-" + str(config.LOGS_DB_TBL[tbl]["days"]) + ",getdate());"
            querySteps.append([sql])

        sql = """
            Delete from ["""+config.LOGS_TBL_COUNT+""""] where not exists
            (Select 1 from
                (Select intDate, tbl From
                    (Select RANK() OVER (Partition by tblDest order by uDate) rnk, uDate as intDate, tblTest as tbl from ["""+config.LOGS_TBL_COUNT+""""]
                     UNION
                     Select RANK() OVER (Partition by tblDest order by uDate desc) rnk, uDate as intDate, tblTest as tbl from ["""+config.LOGS_TBL_COUNT+""""] ) aa
                 Where aa.rnk=1 ) bb
            Where bb.intDate = uDate and bb.tbl=tblDest )
        """

        for connType in config.CONN_URL:
            if "repo" in connType.lower():
                connUrl     = config.CONN_URL[connType]
                connType    = connType.lower()
                connType    = connType.replace("repo","")
                isRepoTblsExists = True
                break

        if isRepoTblsExists:
            execQuery(connType=connType, connString=connUrl, sqlWithParamList=querySteps)
        p ("gFunc->preLogsInDB: DB Config is ON, exec queries: %s" %(str(querySteps)), "ii")
    else:
        p("gFunc->preLogsInDB: DB Config is OFF, do nothing  .... ", "ii")

def logsToDb (js=None):
    if not js:
        js = ""
    isRepoTblsExists = False
    connType   = None
    connUrl    = None
    for connType in config.CONN_URL:
        if "repo" in connType.lower():
            connUrl     = config.CONN_URL[connType]
            connType    = connType.lower()
            connType    = connType.replace("repo","")
            isRepoTblsExists = True
            break

    if isRepoTblsExists:
        # p("gFunc->logsToDb: %s START updating log tables " %(str(js))  , "i")
        totalErrRows = len (config.LOGS_ARR_E)
        totalInfoRows = len(config.LOGS_ARR_I)

        logObj = cnDb (connObject="logs", conType=connType, connUrl=connUrl)
        for tbl in config.LOGS_DB_TBL:
            fList   = config.LOGS_DB_TBL[tbl]["f"]
            logType = config.LOGS_DB_TBL[tbl]["t"]
            tarSQL = "Insert into " + tbl
            tarSQL += " (" + ",".join(fList) + ") "
            tarSQL += "VALUES (" + ",".join(["?" for x in range(len(fList))]) + ")"

            if logType == "error" and totalErrRows>0:
                logObj.cursor.executemany(tarSQL, config.LOGS_ARR_E)
                logObj.conn.commit()
                p("gFunc->logsToDb: ERRORS: Update %s with toal of %s rows " % (str(tbl), str(totalErrRows)), "i")
            elif logType == "info" and totalInfoRows>0:
                logObj.cursor.executemany(tarSQL, config.LOGS_ARR_I)
                logObj.conn.commit()
                p("gFunc->logsToDb: INFO: Update %s with toal of %s rows " % (str(tbl), str(totalInfoRows)), "ii")
            logObj.conn.commit()
        logObj.close()
        #config.LOGS_ARR_E = []
        #config.LOGS_ARR_I = []

def OLAP_Process(serverName,dbName, cubes=[], dims=[], fullProcess=True):
    import sys
    sys.path.append(r'../3rdPart/clrmodule.dll')
    import clr
    clr.AddReference(r"../3rdPart/Microsoft.AnalysisServices.DLL")

    from Microsoft.AnalysisServices import Server
    from Microsoft.AnalysisServices import ProcessType

    processType = ProcessType.ProcessFull if fullProcess else 0
    # Connect to server
    amoServer = Server()
    amoServer.Connect(serverName)

    # Connect to database
    amoDb = amoServer.Databases[dbName]

    for dim in amoDb.Dimensions:
        if len(dims)==0 or dim in dims:
            try:
                dim.Process(processType)
                p(u"gFunc->OLAP_Process, OLAP DB: %s, process DIM %s finish succeffully ... " %(unicode(dbName), unicode(str(dim).decode('windows-1255'))), "i")
            except Exception as e:
                p(u"gFunc->OLAP_Process, OLAP DB: %s, ERROR processing DIM %s ... " % (unicode(dbName),unicode(str(dim).decode('windows-1255'))),"e")
                p(e,"e")

    for cube in amoDb.Cubes:
        if len(cubes)==0 or cube in cubes:
            try:
                cube.Process(processType)
                p(u"gFunc->OLAP_Process, OLAP DB: %s, CUBE %s finish succeffully ... " %(unicode(dbName),unicode(str(cube).decode('windows-1255'))),"i")
            except Exception as e:
                p(u"gFunc->OLAP_Process, OLAP DB: %s, ERROR processing CUBE %s ... " % (unicode(dbName),unicode(str(cube).decode('windows-1255'))),"e")
                p(e,"e")

#### GENERAL FUNCTIONS #####################################################

#### Private function  #####################################################
def parseBNZSql (sql):
    ret = []
    sql = sql.replace ("\n"," ").replace("\t"," ")
    sql = ' '.join ( sql.split() )
    sql = sql.replace (" , ",", ")
    sql = sql.replace('"', '')
    ret.append ('"'+sql+'"')
    sC = sql.lower().find("select ")
    eC = sql.lower().find(" from ")

    if sC>-1 and eC>0:
        sC+=7
        allC = sql[sC:eC].split (",")
        lastC = len (allC)-1
        ret.append ( '\t"sttappend":{' )
        for i, c in enumerate (allC):
            c=c.strip()
            sA = c.lower().find(" as ")
            if sA > 0:
                cSource = c[:sA].strip()
                cTarget = c[sA+4:].strip()


                if "date" in cTarget.lower() or cTarget.startswith("DT"):
                    col = "\t\t" + '"' + cTarget + '":' + '{' + '"s":"' + cSource + '"'
                    col += ',"t":"varchar(10)","f":"fDCast()"},'
                    ret.append(col)
                elif "time" in cTarget.lower():
                    col = "\t\t" + '"' + cTarget + '":' + '{' + '"s":"' + cSource + '"'
                    col += ',"t":"varchar(10)","f":"fTCast()"},'
                    ret.append(col)
        ret.append ('\t\t"ETL_Date":     {"t":"date","f":"fDCurr()"}')


    for r in ret:
        p(r)

def tableToStt (tblName, connUrl, connType='sql'):
    db = cnDb (connObject=tblName, conType=connType, connUrl=connUrl)
    tblCol = db.structure(stt=None,addSourceColumn=True)
    p ('{"target":["'+connType+'","'+tblName+'"],')
    p ('\t"stt":{')
    cntC = len (tblCol)-1
    for i, c in enumerate(tblCol):
        if i == cntC:
            p('\t\t"' + str(c) + '":{"t":"' + str(tblCol[c]['t']) + '"}')
        else:
            p ('\t\t"'+str(c)+'":{"t":"'+str(tblCol[c]['t'])+'"},')
    p ('\t\t}')
    p ('\t}')
    db.close()

import json
from collections import OrderedDict
def jsonToMapping (jFile):
    with open(jFile) as jsonFile:
        jText = json.load(jsonFile, object_pairs_hook=OrderedDict)
        for jMap in jText:
            if u'mapping' in jMap:
                p ("---------------------------------------")
                p (str(jMap[u"source"][1]))
                for col in jMap[u'mapping']:
                    p ('"'+str(jMap[u'mapping'][col])+'":"'+(str(col))+'",')
#### Private function  #####################################################