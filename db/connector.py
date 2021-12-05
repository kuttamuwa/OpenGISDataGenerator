from config import settings
from sqlalchemy import create_engine

dbconf = settings.DB
points_table_name = dbconf.points_table_name
lines_table_name = dbconf.lines_table_name
if_exists = dbconf.if_exists

conn_string = f"postgresql+psycopg2://{dbconf.username}:{dbconf.password}@{dbconf.host}:{dbconf.port}/{dbconf.db}"
db = create_engine(conn_string)