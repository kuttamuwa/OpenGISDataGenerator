"""
Dummy Location Generator

Dependency: OSM (osmnx)

Purpose: Collects

@Author: Umut Ucok, 2021

"""
from dummygen.data_generator import DummyDataManipulator
import argparse

agp = argparse.ArgumentParser()
agp.add_argument('config', help='settings.toml dosyasını yükle')

# publisher = GeoServerPublisher()


if __name__ == '__main__':
    dummy = DummyDataManipulator()
    dummy.generate_points_along_line_osmnx()
    dummy.add_dummy_fields()

    dummy.export_points()
    dummy.export_lines()

