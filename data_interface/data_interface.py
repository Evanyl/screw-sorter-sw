# data_interface.py

import sqlite3
from sqlite3 import Error
import os

from fastener import Screw, Nut, Washer


class ImagingSession:

    def __init__(self, path):

        assert os.path.isdir(path)
        assert 'real' in path or 'sim' in path
        self.path = path
        self.report_path = os.path.join(self.path, 'report.md')
        self.name = os.path.basename(os.path.normpath(self.path))
        self.world = 'real' if 'real' in self.name else 'sim'

        with open(self.report_path, "r") as f:
            lines = [line for line in f.readlines() if ':' in line]
            self.version = lines[0].split(': ')[1].split('\n')[0].strip()
            self.configuration = lines[1].split(': ')[1].split('\n')[0].strip()
            self.date = lines[2].split(': ')[1].split('\n')[0].strip()
            self.start = lines[3].split(': ')[1].split('\n')[0].strip()
            self.end = lines[4].split(': ')[1].split('\n')[0].strip()
            self.operator = lines[5].split(': ')[1].split('\n')[0].strip()

class ScrewQuery:

    measurement_system: list[str]
    processing: list[str]
    length: list[str]
    diameter: list[str]
    pitch: list[str]
    length_n: tuple[float, float]
    diameter_n: tuple[float, float]
    pitch_n: tuple[float, float]
    head: list[str]
    drive: list[str]
    direction: list[str]
    finish: list[str]

    def __init__(self):

        self.measurement_system = []
        self.processing = []
        self.length = []
        self.diameter = []
        self.pitch = []
        self.length_n = (float('-inf'), float('inf'))
        self.diameter_n = (float('-inf'), float('inf'))
        self.pitch_n = (float('-inf'), float('inf'))
        self.head = []
        self.drive = []
        self.direction = []
        self.finish = []

class DataInterface:

    def __init__(self, db, path, create_new_db=False):

        self.root = os.path.basename(path)
        if db == '':
            self.in_memory = True
            self.db = ':memory:'
            self.db_path = self.db
        else:
            self.in_memory = False
            self.db = db
            self.db_path = os.path.join(self.root, self.db)
        
        self.connection = None
        self.c = None

        if create_new_db or self.in_memory:
            self.__create_fresh_db()
        elif self.db in os.listdir(path):
            self.connection = sqlite3.connect(self.db_path)
            self.c = self.connection.cursor()
        else:
            raise Exception(f'{self.db} is not a databse in {path}')
            

    def __create_fresh_db(self):

        if self.in_memory:
            self.connection = sqlite3.connect(self.db)
        else:
            self.connection = sqlite3.connect(os.path.join(self.root, self.db))
        self.c = self.connection.cursor()

        with self.connection:
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
                        processing text,
                        length text,
                        length_n real,
                        diameter text,
                        diameter_n real,
                        pitch text,
                        pitch_n real,
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

    def add_processed_images(self, path, optimized=False):

        assert os.path.isdir(path)
        fasteners = os.listdir(path)

        with self.connection:
            for fastener in fasteners:
                if 'screw' in fastener:
                    screw = Screw(os.path.join(path, fastener))
                    rows = self.c.execute("SELECT * FROM screw WHERE uuid = ?", (screw.uuid,)).fetchall()
                    count = len(rows)
                    if count == 1:
                        row = rows[0]
                        values = vars(screw)
                        values['imaging_session'] = row[2]
                        values['relative_file_path'] = os.path.join(path, fastener)
                        assert values['processing'] != ''
                        self.c.execute('INSERT INTO screw VALUES (:uuid, :world, :imaging_session, :measurement_system, :processing, :length, :length_n, :diameter, :diameter_n, :pitch, :pitch_n, :head, :drive, :direction, :finish,  :relative_file_path)', values)
                    elif count == 0:
                        pass
                    else:
                        pass
                elif 'nut' in fastener:
                    pass
                elif 'washer' in fastener:
                    pass

    def add_imaging_session(self, session_path, optimized=False):

        assert os.path.isdir(session_path)
        img_ses = ImagingSession(session_path)
        
        with self.connection:
            self.c.execute('INSERT INTO imaging_session VALUES (:version, :world, :configuration, :date, :start, :end, :operator)', vars(img_ses))
            session_row_id = self.c.lastrowid
            fasteners = os.listdir(session_path)
            fasteners.remove('report.md')
            for fastener in fasteners:
                if 'screw' in fastener:
                    screw = Screw(os.path.join(session_path, fastener))
                    values = vars(screw)
                    values['imaging_session'] = session_row_id
                    values['relative_file_path'] = os.path.join(session_path, fastener)
                    # assert values['processing'] == ''
                    self.c.execute('INSERT INTO screw VALUES (:uuid, :world, :imaging_session, :measurement_system, :processing, :length, :length_n, :diameter, :diameter_n, :pitch, :pitch_n, :head, :drive, :direction, :finish,  :relative_file_path)', values)
                elif 'nut' in fastener:
                    pass
                elif 'washer' in fastener:
                    pass
                else:
                    raise FileExistsError
            
    def _build_screw_sql_query(self, screw_query:ScrewQuery):

        s = screw_query
        sql = 'SELECT * FROM screw '
        prepend = 'WHERE'
        if len(s.measurement_system) == 0:
            pass
        elif len(s.measurement_system) == 1:
            sql  += f'WHERE measurement_system = \'{s.measurement_system[0]}\' '
            prepend = 'AND'
        else:
            sql += f'WHERE measurement_system IN {(format(tuple(s.measurement_system)))} '
            prepend = 'AND'
        if len(s.processing) == 0:
            pass
        elif len(s.processing) == 1:
            sql  += f'{prepend} processing = \'{s.processing[0]}\' '
            prepend = 'AND'
        else:
            sql += f'{prepend} processing IN {(format(tuple(s.processing)))} '
            prepend = 'AND'
        if len(s.length) == 0:
            pass
        elif len(s.length) == 1:
            sql  += f'{prepend} length = \'{s.length[0]}\' '
            prepend = 'AND'
        else:
            sql += f'{prepend} length IN {(format(tuple(s.length)))} '
            prepend = 'AND'
        if len(s.diameter) == 0:
            pass
        elif len(s.diameter) == 1:
            sql  += f'{prepend} diameter = \'{s.diameter[0]}\' '
            prepend = 'AND'
        else:
            sql += f'{prepend} diameter IN {(format(tuple(s.diameter)))} '
            prepend = 'AND'
        if len(s.pitch) == 0:
            pass
        elif len(s.pitch) == 1:
            sql  += f'{prepend} pitch = \'{s.pitch[0]}\' '
            prepend = 'AND'
        else:
            sql += f'{prepend} pitch IN {(format(tuple(s.pitch)))} '
            prepend = 'AND'
        if s.length_n[0] == float('-inf'):
            pass
        else:
            sql += f'{prepend} length_n >= {s.length_n[0]} '
            prepend = 'AND'
        if s.length_n[1] == float('inf'):
            pass
        else:
            sql += f'{prepend} length_n <= {s.length_n[1]} '
            prepend = 'AND'
        if s.diameter_n[0] == float('-inf'):
            pass
        else:
            sql += f'{prepend} diameter_n >= {s.diameter_n[0]} '
            prepend = 'AND'
        if s.diameter_n[1] == float('inf'):
            pass
        else:
            sql += f'{prepend} diameter_n <= {s.diameter_n[1]} '
            prepend = 'AND'
        if s.pitch_n[0] == float('-inf'):
            pass
        else:
            sql += f'{prepend} pitch_n >= {s.pitch_n[0]} '
            prepend = 'AND'
        if s.pitch_n[1] == float('inf'):
            pass
        else:
            sql += f'{prepend} pitch_n <= {s.pitch_n[1]} '
            prepend = 'AND'
        if len(s.head) == 0:
            pass
        elif len(s.head) == 1:
            sql  += f'{prepend} head = \'{s.head[0]}\' '
            prepend = 'AND'
        else:
            sql += f'{prepend} head IN {(format(tuple(s.head)))} '
            prepend = 'AND'
        if len(s.drive) == 0:
            pass
        elif len(s.drive) == 1:
            sql  += f'{prepend} drive = \'{s.drive[0]}\' '
            prepend = 'AND'
        else:
            sql += f'{prepend} drive IN {(format(tuple(s.drive)))} '
            prepend = 'AND'
        if len(s.direction) == 0:
            pass
        elif len(s.direction) == 1:
            sql  += f'{prepend} direction = \'{s.direction[0]}\' '
            prepend = 'AND'
        else:
            sql += f'{prepend} direction IN {(format(tuple(s.direction)))} '
            prepend = 'AND'
        if len(s.finish) == 0:
            pass
        elif len(s.finish) == 1:
            sql  += f'{prepend} finish = \'{s.finish[0]}\' '
            prepend = 'AND'
        else:
            sql += f'{prepend} finish IN {(format(tuple(s.finish)))} '
            prepend = 'AND'
        return sql.strip()


    def get_screw_images(self, screw_query:ScrewQuery):

        sql = self._build_screw_sql_query(screw_query)
        rows = self.c.execute(sql).fetchall()
        uuids = [row[0] for row in rows]
        filepaths = [row[-1] for row in rows]
        return uuids, filepaths









