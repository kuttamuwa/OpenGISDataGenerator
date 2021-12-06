"""
If you deployed GeoServerPublisher and try to add Oracle SDO as DataStore, follow these:

- Download plugin:
https://docs.geoserver.org/latest/en/user/data/database/oracle.html#oracle-install
Extension page in GeoServerPublisher download.

- If you get an error about character set and says put orai18n.jar into classpath:
https://www.oracle.com/database/technologies/jdbc-drivers-12c-downloads.html

Put all of them into
C:\geoserver-2.19.2\webapps\geoserver\WEB-INF\lib

"""
