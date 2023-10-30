# fastener.py

import os
import json
from abc import ABC, abstractmethod

class Fastener(ABC):

    status = ['ok', 'stale']
    world = ['real', 'sim']
    platform_version = {'real': [1.0], 'sim': [1.0]}
    platform_configuration = {'real': [0], 'sim': [0]}
    measurement_system = ['metric', 'imperial']
    fastener_type = ['screw', 'nut', 'washer']
    processing = ['', 'binary_1', 'dft_1']

    path: str
    uuid: str
    status: str
    world: str
    platform_version: str
    platform_configuration: str
    date: str
    time: str
    measurement_system: str
    fastener_type: str
    processing: str

    def __init__(self, path:str):
        assert os.path.isdir(path)
        self.path = path
        metadata_file = [file for file in os.listdir(self.path) if 'json' in file][0]
        metadata_path = os.path.join(self.path, metadata_file)

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            self.uuid = metadata['uuid']
            self.status = metadata['status']
            self.world = metadata['world']
            self.platform_version = metadata['platform_version']
            self.platform_configuration = metadata['platform_configuration']
            self.date = metadata['date']
            self.time = metadata['time']
            self.measurement_system = metadata['measurement_system']
            self.fastener_type = metadata['fastener_type']
            self.processing = metadata['processing'] if 'processing' in metadata else ''
            self._populate_attributes(metadata)
    
    def __str__(self):

        return str(vars(self))

    @abstractmethod
    def _populate_attributes(self, metadata):
        pass
        
class Screw(Fastener):

    length = {'metric': ['1', '2'], 'imperial': ['1', '2']}
    diameter = {'metric': ['1', '2'], 'imperial': ['1', '2']}
    pitch = {'metric': ['1', '2'], 'imperial': ['1', '2']}
    length_n = (0.0001, 100)
    pitch_n = (0.0001, 100)
    diameter_n = (0.0001, 100)
    head = ['socket']
    drive = ['hex', 'torx', 'phillips']
    direction = ['right', 'left']
    finish = ['galvanized', 'steel']

    length: str
    diameter: str
    pitch: str
    length_n: float
    diameter_n: float
    pitch_n: float
    head: str
    drive: str
    direction: str
    finish: str

    def __init__(self, path:str):
        super().__init__(path)

    def _populate_attributes(self, metadata):
        self.head = metadata['attributes']['head']
        self.drive = metadata['attributes']['drive']
        self.direction = metadata['attributes']['direction']
        self.finish = metadata['attributes']['finish']
        self.length = metadata['attributes']['length']
        self.diameter = metadata['attributes']['diameter']
        self.pitch = metadata['attributes']['pitch']
        if self.measurement_system == 'metric':
            self.length_n = float(metadata['attributes']['length'])
            self.diameter_n = float(metadata['attributes']['diameter'])
            self.pitch_n = float(metadata['attributes']['pitch'])
        elif self.measurement_system == 'imperial':
            pass

class Nut(Fastener):

    diameter: str
    pitch: str
    direction: str
    finish: str

    def __init__(self, path:str):
        super().__init__(path)

    def _populate_attributes(self, metadata):
        self.diameter = metadata['attributes']['diameter']
        self.pitch = metadata['attributes']['pitch']
        self.direction = metadata['attributes']['direction']
        self.finish = metadata['attributes']['finish']

class Washer(Fastener):

    inner_diameter: str
    outer_diameter: str
    thickness: str
    finish: str

    def __init__(self, path:str):
        super().__init__(path)

    def _populate_attributes(self, metadata):
        self.inner_diameter = metadata['attributes']['inner_diameter']
        self.outer_diameter = metadata['attributes']['outer_diameter']
        self.thickness = metadata['attributes']['thickness']
        self.finish = metadata['attributes']['finish']