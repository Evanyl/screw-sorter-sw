# imaging_session.py 

import os

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
