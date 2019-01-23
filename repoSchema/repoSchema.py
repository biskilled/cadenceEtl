import sys
sys.path.append("../")
from lib.popeye.config import config
config.CONNECTIONS_ACTIVE = {"sql": "cnDb"}
import lib.popeye.mapp.mapper as mapper

config.CONN_URL   = {'sql' : "DRIVER={SQL Server};SERVER=SRV-BI,1433;DATABASE=BZ_AUT;UID=bpmk;PWD=bpmk;",
                     'sqlRepo': "DRIVER={SQL Server};SERVER=SRV-BI,1433;DATABASE=BZ_AUT;UID=bpmk;PWD=bpmk;"}

config.DIR_DATA     =  "./"

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Loading data from json files, cant get: source list files or destination list files or append mode () ')
    mapper.loadJson()