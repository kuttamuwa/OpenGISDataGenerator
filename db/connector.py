import platform
from pymongo import MongoClient
from sqlalchemy import create_engine

from config import settings

dbconf = settings.DB
mongo_choice = dbconf.mongo
points_table_name = dbconf.points_table_name
lines_table_name = dbconf.lines_table_name
pois_point_table_name = dbconf.poi_points_table_name
pois_polygon_table_name = dbconf.pois_polygon_table_name

if_exists = dbconf.if_exists

pg_conn_string = f"postgresql+psycopg2://postgres:figo1190@localhost:5432/riskreferencedb"

if mongo_choice == 1:
    if platform.system() == 'Windows':
        db = MongoClient()
    else:
        db = MongoClient(username=dbconf.username,
                         password=dbconf.password,
                         host=dbconf.host,
                         port=dbconf.port)
elif mongo_choice == 0:
    db = create_engine(pg_conn_string)
