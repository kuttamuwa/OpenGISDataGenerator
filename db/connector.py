from config import settings
from sqlalchemy import create_engine
from pymongo import MongoClient

dbconf = settings.DB
mongo_choice = dbconf.mongo
points_table_name = dbconf.points_table_name
lines_table_name = dbconf.lines_table_name
pois_point_table_name = dbconf.poi_points_table_name
pois_polygon_table_name = dbconf.poi_polygon_table_name

if_exists = dbconf.if_exists

conn_string = f"postgresql+psycopg2://{dbconf.username}:{dbconf.password}@{dbconf.host}:{dbconf.port}/{dbconf.db}"

if mongo_choice == 1:
    db = MongoClient()
elif mongo_choice == 0:
    db = create_engine(conn_string)