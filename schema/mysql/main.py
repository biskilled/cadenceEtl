import sys
sys.path.append("../")
from config import config
import lib.popeye.mapp.mapper as mapper
import lib.popeye.loader.loader as loader

config.CONN_TYPES = {
                        #'sql'   :"DRIVER={SQL Server};SERVER=SRV-BI,1433;DATABASE=DW_AUT;UID=bpmk;PWD=bpmk;",
                        'sql'   :"DRIVER={SQL Server};SERVER=JJ-TALS,1433;DATABASE=CDRDW;UID=tals;PWD=tals;",
                        'mysql' : {"host":"vertica-test-1.tuenti.int", "user":"bi", "passwd":"delegated3206", "db":"sampled_mirror_operational"},
                        'vertica': {'host': 'vertica-test-1.tuenti.int','port': 5433, 'user':'tuenti', 'password':'vertica', 'database':"tuenti", 'read_timeout':600, 'unicode_error':'strict', 'ssl':False, 'connection_timeout':5},
                        'file'  :{'delimiter':'~','header':True, 'folder':"C:\\bi\\data\\automation"}
                    }

config.DIR_DATA     =  "C:\\bitbucket\\mapper\\mysql"

#mapper.loadJson()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Loading data from json files, cant get: source list files or destination list files or append mode () ')

    mapper.loadJson()

    loader.loading(appendData=False, sourceList=None, destList=None)  # destList=[u'AUT_M_OVED2']
    #main ()

#loader.loading()

