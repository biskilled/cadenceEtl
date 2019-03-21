import io, re

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

        post = re.sub(r"--.*$", r"",    post, flags= re.IGNORECASE | re.MULTILINE | re.UNICODE  ).replace ("--","")
        post = re.sub(r'\/\*.*\*\/',    "", post, flags=re.IGNORECASE | re.MULTILINE | re.UNICODE | re.DOTALL )
        post = re.sub(r"print .*$", r"",post, flags=re.IGNORECASE | re.MULTILINE | re.UNICODE ).replace ("print ","")

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
        # Delete all rows which are not relevant
        # Regex : <!popEtl XXXX/>
        #fPythonNot = re.search(r"<!%s([^>].*)/>" % (mWorld), query,flags=re.IGNORECASE | re.MULTILINE | re.UNICODE | re.DOTALL | re.S)
        # Regex : <!popEtl> ......... </!popEtl>
        reg = re.finditer(r"<!%s(.+?)</!%s>" % (mWorld, mWorld), query,flags=re.IGNORECASE | re.MULTILINE | re.UNICODE | re.DOTALL | re.S )
        if reg:
            for regRemove in reg:
                query = query.replace (regRemove.group(0),"")

        # Add python queries into return list
        # Regex : <popEtl STRING_NAME> ....... </popEtl>
        #fPython2    = re.search(r"<%s.*/%s>" % (mWorld,mWorld),   query, flags = re.IGNORECASE | re.MULTILINE | re.UNICODE | re.DOTALL | re.S)

        # Regex : <popEtl STRING_NAME>......</popEtl> --> Take string to the end
        reg = re.finditer(r"<%s(.+?)>(.+?)</%s>" %(mWorld,mWorld), query,flags=re.IGNORECASE | re.MULTILINE | re.UNICODE | re.DOTALL | re.S)

        if reg:
            for i, regFind in enumerate (reg):
                pythonSeq = regFind.group(0)
                pythonVar = regFind.group(1).strip()
                querySql  = regFind.group(2).strip()

                if i == 0 and regFind.start()>0:
                    queryStart = query[: query.find(pythonSeq)].strip()
                    if queryStart and len (queryStart)>0:
                        ret.append((None, queryStart))

                ret.append((pythonVar, querySql))
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

def _replaceStr (sString,findStr, repStr, ignoreCase=True):
    if ignoreCase:
        pattern = re.compile(re.escape(findStr), re.IGNORECASE)
        res = pattern.sub (repStr, sString)
    else:
        res = sString.replace (findStr, repStr)
    return res

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
                pr2= ( _replaceStr(sString=pr2, findStr=prop, repStr=dicProp[prop], ignoreCase=True) )

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

