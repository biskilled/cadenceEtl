
from popEtl import CONFIG, Model, TEST

CONFIG.CONNECTION_URL = {
    'sqllite':{"type":"sqlite","url":"./sampleDb"},
    'file':"./result.csv"
}

TEST()

CONFIG.CON_DIR_DATA = "C:\\gitHub\\popEtl\\lib\\popEtl\\samples\\sampleHealthCare\\"
CONFIG.LOGS_DIR     = CONFIG.CON_DIR_DATA+"logs"
CSV_SOURCE          = CONFIG.CON_DIR_DATA+"csvData"


# load data from CSV to sqlite.
dic = [{"source": ["file",CSV_SOURCE+"\\DEMOGRAPHICS.csv"],
       "target": ["sqllite","demographics"] }]

Model(dicObj=dic, sourceList=None, destList=None)
# load data from sqllite into DWH
# transfer data into csv back







