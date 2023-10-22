# data_interface.py

import sqlite3
import os

from imaging_session import ImagingSession
from fastener import Screw, Nut, Washer

class DataInterface:

    def __init__(self, db, data_path):

        self.root = os.path.basename(data_path)
        if (db == ''):
            self.__create_fresh_db()
        else:
            self.connection = sqlite3.connect(db)
            self.c = self.connection.cursor()

    def __create_fresh_db(self):

        self.connection = sqlite3.connect(':memory:')
        self.c = self.connection.cursor()

        self.c.execute("""CREATE TABLE imaging_session (
            version real,
            world text,
            configuration integer, 
            date text,
            start_time text,
            end_time text,
            operator text
        )""")

        self.c.execute("""CREATE TABLE screw (
                       uuid text,
                       world text,
                       imaging_session integer,
                       measurement_system text,
                       length text,
                       diameter text,
                       pitch text,
                       head text,
                       drive text,
                       direction text,
                       finish text,
                       relative_file_path text
        )""")

        self.c.execute("""CREATE TABLE nut (
                       id integer primary key, 
                       uuid text,
                       world text,
                       imaging_session integer,
                       measurement_system text,
                       diameter text,
                       pitch text,
                       direction text,
                       finish text,
                       relative_file_path text
        )""")

        self.c.execute("""CREATE TABLE washer (
                       id integer primary key, 
                       uuid text,
                       world text,
                       imaging_session integer,
                       measurement_system text,
                       inner_diameter text,
                       outer_diameter text,
                       thickness text,
                       finish text,
                       relative_file_path text
        )""")

    def add_imaging_session(self, session_path, optimized=False):

        assert os.path.isdir(session_path)
        new = ImagingSession(session_path)
        self.c.execute('INSERT INTO imaging_session VALUES (:version, :world, :configuration, :date, :start, :end, :operator)', vars(new))
        session_row_id = self.c.lastrowid
        print(session_row_id)
        fasteners = os.listdir(session_path)
        fasteners.remove('report.md')

        for fastener in fasteners:

            if 'screw' in fastener:
                screw = Screw(os.path.join(session_path, fastener))
                values = vars(screw)
                values['imaging_session'] = session_row_id
                values['relative_file_path'] = os.path.join(session_path, fastener)
                self.c.execute('INSERT INTO screw VALUES (:uuid, :world, :imaging_session, :measurement_system, :length, :diameter, :pitch, :head, :drive, :direction, :finish,  :relative_file_path)', values)
            elif 'nut' in fastener:
                nut = Nut(os.path.join(session_path, fastener))
            elif 'washer' in fastener:
                washer = Washer(os.path.join(session_path, fastener))
            else:
                raise FileExistsError
        
        # print(os.listdir(session_path).remove('report.md'))









