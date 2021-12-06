"""
Dummy Location Generator

Dependency: OSM (osmnx)

Purpose: Collects

@Author: Umut Ucok, 2021

"""
from dummygen.data_generator import DummyDataGenerator
import argparse

agp = argparse.ArgumentParser()
agp.add_argument('config', help='settings.toml dosyasını yükle')


if __name__ == '__main__':
    dummy = DummyDataGenerator()
    dummy.generate_points_along_line()
    dummy.add_dummy_fields_grouping()

    dummy.export_points()
    dummy.export_lines()

