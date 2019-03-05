import io, re

from popEtl.glob.glob import replaceStr

def _removeComments (listQuery, endOfLine='\n'):
    retList = []
    for s in listQuery:
        isTup = False
        if isinstance(s, (tuple, list) ):
            pre = s[0].strip() if s[0] else None
            post= s[1].strip()
            isTup = True
        else:
            post = s.strip()
        post = re.sub(r"--.*",          "", post, flags=re.IGNORECASE | re.MULTILINE | re.UNICODE | re.S )
        post = re.sub(r'\/\*.*\*\/',    "", post, flags=re.IGNORECASE | re.MULTILINE | re.UNICODE | re.DOTALL )
        post = re.sub(r"print .*[$\n]", "", post, flags=re.IGNORECASE | re.MULTILINE | re.UNICODE | re.S )

        if endOfLine:
            while len (post)>1 and post[0:1] == "\n":
                post = post[1:]

            while len (post)>1 and post[-1:] == "\n":
                post = post[:-1]

        if not post or len(post) == 0:
            continue
        else:
            if isTup:
                retList.append ( (pre,post,) )
            else:
                retList.append (post)

    return retList

def _getPythonParam (queryList, mWorld="popEtl"):
    ret = []
    for query in queryList:
        # fPython1 = re.search(r"<%s>.[^<]*</%s>" %(mWorld, mWorld), sql, re.I|re.M|re.S|re.U )
        fPython     = re.search(r"<%s([^>].*)/>" % (mWorld), query, re.I | re.M | re.S | re.U)
        fPythonNot  = re.search(r"<!%s([^>].*)/>" % (mWorld), query, re.I | re.M | re.S | re.U)
        if fPython:
            pythonSeq = fPython.group(0)
            pythonVar = fPython.group(1).strip()
            querySql  = query[ query.find(pythonSeq)+len(pythonSeq) : ]
            queryStart= query[ : query.find(pythonSeq) ].strip()
            if queryStart and len (queryStart)>0:
                ret.append((None, queryStart))
            ret.append ( (pythonVar, querySql) )
        elif fPythonNot:
            pythonSeq = fPythonNot.group(0)
            querySql = query[query.find(pythonSeq) + len(pythonSeq):]
            queryStart = query[: query.find(pythonSeq)].strip()
            if queryStart and len (queryStart)>0:
                ret.append((None, queryStart))
            ret.append(("~", querySql))
        else:
            if query and len(query.strip()) > 0:
                ret.append ( (None, query.strip()) )

    return ret

def _getAllQuery (longStr, splitParam = ['GO',u';']):
    sqlList = []
    for splP in splitParam:
        if len(sqlList) == 0:
            sqlList = longStr.split (splP)
        else:
            tmpList = list([])
            for sql in sqlList:
                tmpList.extend (sql.split(splP))
            sqlList = tmpList
    return sqlList

def _replaceProp(allQueries, dicProp):
    ret = []
    for query in allQueries:
        if isinstance(query, (list,tuple)):
            pr1 = query[0]
            pr2 = query[1]
        else:
            pr2 = query
        if not pr1 or pr1 and pr1!="~":
            for prop in dicProp:
                pr2= ( replaceStr(sString=pr2, findStr=prop, repStr=dicProp[prop], ignoreCase=True) )

        tupRet = (pr1, pr2,) if isinstance(query, (list,tuple)) else pr2
        ret.append (tupRet)
    return ret

def queryParsetIntoList (sqlScript, getPython=True, removeContent=True, dicProp=None, pythonWord="popEtl"):
    if isinstance(sqlScript, (tuple,list)):
        sqlScript = "".join(sqlScript)
    # return list of sql (splitted by list of params)
    allQueries = _getAllQuery(longStr=sqlScript, splitParam = ['GO',u';'])

    if getPython:
        allQueries = _getPythonParam(allQueries, mWorld=pythonWord)

    if removeContent:
        allQueries = _removeComments(allQueries)

    if dicProp:
        allQueries = _replaceProp(allQueries, dicProp)

    return allQueries

with io.open('./sqlQuery.sql', 'r',  encoding='utf-8') as inp:
    sqlScript = inp.readlines()
    dicProp = {"@c1":"cccccc","@f1":"ppppp","@f2":"123456","@f3":"vcvcvcvcvcvcc"}
    queryList = queryParsetIntoList (sqlScript, getPython=True, removeContent=True, pythonWord="popEtl",dicProp=dicProp)

    for ret in queryList:
        print ("-----------------------------------------")
        print (ret)