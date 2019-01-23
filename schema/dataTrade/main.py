import sys
sys.path.append("../")
from config import config
import lib.popeye.mapp.mapper as mapper

# 'sql'   :"DRIVER={SQL Server};SERVER=TAL-LENOVO,1433;DATABASE=trading;UID=tals;PWD=tals;"
# 'sql'   :"DRIVER={SQL Server};SERVER=JJ-TALS,1433;DATABASE=tr;UID=tals;PWD=tals;"

# "C:\\Python27\\apps\\mapper\\dataTrade"
# "C:\\bitbucket\\mapper\\dataTrade"

config.CONN_TYPES   ={
                        'sql'   :"DRIVER={SQL Server};SERVER=JJ-TALS,1433;DATABASE=tr;UID=tals;PWD=tals;"
                     }
config.DIR_DATA     =  "C:\\bitbucket\\mapper\\dataTrade"

mapper.loadJson()