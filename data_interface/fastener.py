# fastener.py

import os
import json
from abc import ABC, abstractmethod

class Fastener(ABC):

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
            self.populate_attributes(metadata)

    @abstractmethod
    def populate_attributes(self, metadata):
        pass
        
class Screw(Fastener):

    length: str
    diameter: str
    pitch: str
    head: str
    drive: str
    direction: str
    finish: str

    def __init__(self, path:str):
        super().__init__(path)

    def populate_attributes(self, metadata):
        self.length = metadata['attributes']['length']
        self.diameter = metadata['attributes']['diameter']
        self.pitch = metadata['attributes']['pitch']
        self.head = metadata['attributes']['head']
        self.drive = metadata['attributes']['drive']
        self.direction = metadata['attributes']['direction']
        self.finish = metadata['attributes']['finish']

class Nut(Fastener):

    diameter: str
    pitch: str
    direction: str
    finish: str

    def __init__(self, path:str):
        super().__init__(path)

    def populate_attributes(self, metadata):
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

    def populate_attributes(self, metadata):
        self.inner_diameter = metadata['attributes']['inner_diameter']
        self.outer_diameter = metadata['attributes']['outer_diameter']
        self.thickness = metadata['attributes']['thickness']
        self.finish = metadata['attributes']['finish']