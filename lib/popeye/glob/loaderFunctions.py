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

import re
import datetime

class fncBase ():
    def __init__(self,*args, **kargs):
        self.cDate = datetime.datetime.today().strftime('%m/%d/%y')

    def handler(self, col): pass

class fDCast(fncBase):
    def __init__(self, *args, **kargs):
        fncBase.__init__(self, *args, **kargs)

    def handler(self, col):
        if not col:
            return self.cDate
        if len(col)!=8 or not col.isdigit ():
            return None

        yy = col[:4]
        mm = col[4:6]
        dd = col[6:8]

        if yy=="0000" or yy=="9999" or len(yy.strip())<4:
            return None

        if yy<'1900' :
            return '01/01/2006'
        if yy>'2050' :
            yy = '2050'
        return None if yy == "9999" else "%s/%s/%s" % (mm, dd, yy)

class fDTCast(fncBase):
    def __init__(self, *args, **kargs):
        fncBase.__init__(self, *args, **kargs)

    def handler(self, col):
        hh = '00'
        min= '00'
        ss = '00'
        yy = "0000"
        mm = '00'
        dd = '00'

        if not col:
            return None

        if len (col)>=8 and col.isdigit ():
            yy = col[:4]
            mm = col[4:6]
            dd = col[6:8]

            if len(col) == 14 :
                hh = col[8:10]
                min = col[10:12]
                ss = col[12:14]

                if hh == "24":
                    hh = "00"

            if yy=="0000" or yy=="9999" or len(yy.strip())<4:
                return None

            if yy<'1900' :
                return '01/01/2006'

            if yy>'2050':
                yy = "2050"

        return None if yy == "0000" or yy=="9999" else "%s/%s/%s %s:%s:%s" % (mm, dd, yy, hh,min,ss)

class fDFile(fncBase):
    def __init__(self, *args, **kargs):
        fncBase.__init__(self, *args, **kargs)

    def handler(self, col):
        if not col or len(col)==0:
            return col
        col = col[:10].split("/")

        if len(col)==3:
            yy = col[2]
            mm = col[1]
            dd = col[0]

            return "%s/%s/%s" % (mm, dd, yy)
        col = col[:10].split("-")
        if len(col)==3:
            yy = col[0]
            mm = col[1]
            dd = col[1]
            return "%s/%s/%s" % (mm, dd, yy)

        return None

class fDCurr(fncBase):
    def __init__(self, *args, **kargs):
        fncBase.__init__(self, *args, **kargs)

    def handler(self, col):
         return self.cDate

class fTCast(fncBase):
    def __init__(self, *args, **kargs):
        fncBase.__init__(self, *args, **kargs)

    def handler(self, col):
        if not col or "000000" in col:
            return None
        hh = col[:2]
        mm = col[2:4]
        ss = col[4:6]
        return  "23:59:29" if "24" in hh else "%s:%s:%s" % (hh, mm, ss)

class fR(fncBase):
    def __init__(self, *args, **kargs):
        fncBase.__init__(self, *args, **kargs)
        self.rep0 = args[0]
        self.rep2 = args[1]

    def handler(self, col):
        if col and isinstance(col, str):
            return col.replace (self.rep0, self.rep2)
        return col

class fNull(fncBase):
    def __init__(self, *args, **kargs):
        fncBase.__init__(self, *args, **kargs)
        self.rep0 = args[0]

    def handler(self, col):
        if not col or len (col.strip()) == 0:
            return self.rep0
        return col

class fClob(fncBase):
    def __init__(self, *args, **kargs):
        fncBase.__init__(self, *args, **kargs)

    def handler(self, col):
        if not col:
            return None
        #if type(col) == cx_Oracle.LOB:
            #print (str(col).encode("windows-1255"))
            #    print "Yoooooooooooooooooooooooooooooooooo"
            #    return str(col)
            #else:
            #    return None
            # return str(col)

        return col


#############################OLD  ATTEMT #############################################################

class fPhone (fncBase):
    def __init__(self, *args, **kargs):
        fncBase.__init__(self, *args, **kargs)

    def handler(self, col):
        phone = re.sub(r'\D', '', col)
        return phone

class fDecode (fncBase):
    def __init__(self, *args, **kargs):
        fncBase.__init__(self, *args, **kargs)
        self.xx = "Nothing"
        if len(args)>0: self.xx = args[0]

    def handler(self, col):
        #print ("this is " + str(col))
        #print (self.xx)
        return str(col)+" sss"

class fAddress (fncBase):
    def __init__(self, *args, **kargs):
        fncBase.__init__(self, *args, **kargs)
        self.adressType = ""
        if len(args)>0:
            self.adressType = args[0]

    def handler(self, col):
        # print ("this is " + col)
        return col+self.adressType

# tt = fnDecode ("xxrr")
# tt.foldHandler ("hhhhh")
# test()


