# Installation
## Install Anaconda 
Python: 3.10

Install OSMnX:
https://osmnx.readthedocs.io/en/stable/

conda config --prepend channels conda-forge
conda create -n oxenv --strict-channel-priority osmnx

## To install libraries
conda env update --name oxenv --file req.yml

# Deployment
python main.py

# Config
settings.toml
Details are specified below:

[DUMMY]:
[LOCATION SETTINGS]
bbox: Boundary box used by shapely. Shapely uses this if use_osmnx = False
address: Open address. Ex: 'Bucharest, Romania'

[POI SETTINGS]
poi_center: Point of interest center coordinate. OSM uses this to download POI data. 
It doesn't work if you set use_osmnx=True
poi_buffer_distance = OSM downloads points within 1000 meters of buffered area on poi center. 
Unit is meters, Default: 1000

[OSM SETTINGS]
network_type = "all_private"  Choices:
"all_private", "all", "bike", "drive", "drive_service", "walk"

[DATE SETTINGS]
start_date = "2019-8-03 16:40:21"
end_date = "2021-12-03 15:40:21"
date_mixing = "True"  # Generate random date specified start_date-end_date or assign each as start_date

reload = "False"  # points table will be dropped and creates again if set True. Otherwise, it will append
crs = "epsg:3857"  # coordinate system. Use EPSG ! Geographic cs is epsg:4326

[STATIC POINTS]
run = 1 means RUN, else means DO NOT RUN
sample_count = 2000  # how many static points should be added?
recursive_sample = 200  # we will duplicate 20 rows of generated points for each step till repeated_times

[RECURSIVE POINTS]
run = 1 means RUN, else means DO NOT RUN
repeated_times = Default: 3. Specifies how many times do you want to create point. Each step the program takes
sample of "recursive_sample" and append points as geometric duplicated.
wait_min = How many minutes you want them to add timestamp for each?

[DYNAMIC POINTS]
run = 1 means RUN, else means DO NOT RUN
minimum_distance = 50  # minimum footstep meters
maximum_distance = 120 # max footstep meters
avg_speed = 1.4 # pedestrian speed: m/s

[DATA DOWNLOAD]
use_osmnx = Deploys graph and downloads line if set True. Works offline if set False and creates points with shapely
Shapely uses bbox to generate random points.

poi_tags = See https://wiki.openstreetmap.org/wiki/Map_features#Entertainment.2C_Arts_.26_Culture
There is an example in the config. You can change it if you want to add other types of data. 
Program will append newest data as dropping duplicates.