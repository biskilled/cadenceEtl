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

from popEtl.config import config
from popEtl.glob.glob import p
from popEtl.loader.loadExecSP import execQuery
from popEtl.connections.connector import connector

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

def OLAP_Process(serverName,dbName, cubes=[], dims=[], fullProcess=True):
    import sys, os
    print (sys.path)
    sys.path.append(os.path.abspath(r'../../3rdPart/clrmodule.dll'))
    import clr
    clr.AddReference(os.path.abspath(r"../../3rdPart/Microsoft.AnalysisServices.DLL"))

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
    db = connector (connType=connType, connUrl=connUrl,connObj=tblName)
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