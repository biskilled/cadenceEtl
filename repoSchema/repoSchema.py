import sys
sys.path.append("../")
from popEtl.config import config
config.CONNECTIONS_ACTIVE = {"sql": "cnDb"}
import popEtl.mapp.mapper as mapper

config.CONN_URL   = {'sql' : "DRIVER={SQL Server};SERVER=XXXXX;DATABASE=YOYOYO;UID=YOYOYO;PWD=YOYOYO;",
                     'sqlRepo': "DRIVER={SQL Server};SERVER=XXXXX,1433;DATABASE=YOYOYO;UID=YOYOYO;PWD=YOYOYO;"}

config.DIR_DATA     =  "./"

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Loading data from json files, cant get: source list files or destination list files or append mode () ')
    mapper.loadJson()