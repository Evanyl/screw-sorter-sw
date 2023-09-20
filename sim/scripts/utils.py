import cadquery as cq
import itertools
import logging
import random

from pathlib import Path
from typing import Dict

URL = "https://www.mcmaster.com"
REQUIRED_SEARCH_KEYS_SCREW = [
    "fastener-head-type",
    "thread-size",
    "length",
]
OPTIONAL_SEARCH_KEYS_SCREW = []
SEARCH_KEYS_SCREW = REQUIRED_SEARCH_KEYS_SCREW + OPTIONAL_SEARCH_KEYS_SCREW
SUPPORTED_FASTENER_TYPES = ["screws"]

class McmasterSearcher:
    """
    This will keep track of permuting through the given search params
    """
    def __init__(self, search_params: Dict[str, str]):
        self.search_params = search_params
        self.fastener_type = self.search_params.pop("fastener-type")
        self.search_params_keys = list(self.search_params.keys())
        self.verify_valid_search_params()

        self.combinations = self.build_internal_combinations()
        random.shuffle(self.combinations)

    def verify_valid_search_params(self):
        assert self.fastener_type in SUPPORTED_FASTENER_TYPES, f"{self.fastener_type} is not supported right now"

        search_params_keys = set(self.search_params.keys())
        assert len(search_params_keys) == len(self.search_params.keys()), "Search param keys are duplicated"

        if self.fastener_type == "screws":
            missing_required_keys = set(REQUIRED_SEARCH_KEYS_SCREW) - search_params_keys
            assert not missing_required_keys, f"Missing search params: {missing_required_keys}"
            
            unsupoported_keys = search_params_keys - set(SEARCH_KEYS_SCREW)
            assert not unsupoported_keys, f"Unsupported or misspelt search params: {unsupoported_keys}"

    def build_internal_combinations(self):
        return list(itertools.product(*list(self.search_params.values())))

    def next(self):
        if self.is_done():
            return None

        curr = self.combinations.pop()
        url = f"{URL}/products/{self.fastener_type}"
        for i in range(len(curr)):
            key = self.search_params_keys[i]
            value = curr[i]
            url = f"{url}/{key}~{value}"

        return url

    def is_done(self):
        return not self.combinations
    
def convert_step_to_stl(step_file_path: Path, output_file_path: Path):
    assert step_file_path.exists(), f"{step_file_path} does not exist"

    step_object = cq.importers.importStep(str(step_file_path))
    cq.exporters.export(step_object, str(output_file_path))

    assert output_file_path.exists(), f"{output_file_path} was not successfully created, silent error somewhere"
