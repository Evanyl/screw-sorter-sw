import click
import json
import logging
import os
from subprocess import CalledProcessError, run, TimeoutExpired, PIPE, STDOUT
import uuid

from pathlib import Path

RETRIES = 3

@click.command(help="Run blender sim")
@click.option("--input_folder_path", "input_folder_path", required=True, help="Input folder with donloaded CAD models")
@click.option("--output_folder_path", "output_folder_path", required=True, help="Output folder to put generated images")
@click.option("--copies", "copies", required=True, help="Number of copies for each fastener")
@click.option("--timeout", "timeout", required=True, help="Timeout for generation")
def main(input_folder_path, output_folder_path, copies, timeout):

    input_folder_path = Path(input_folder_path)
    assert input_folder_path.exists(), f"{input_folder_path} does not exist"
    output_folder_path = Path(output_folder_path)
    assert output_folder_path.exists(), f"{output_folder_path} does not exist"

    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler(output_folder_path / "debug.log"),
            logging.StreamHandler(),
        ]
    )
    cad_models = [d for d in os.listdir(input_folder_path) if os.path.isdir(input_folder_path / d)]
    logging.info(f"{len(cad_models)} total")

    for model in cad_models:
        for copy in copies:
            # Retries
            for attempt in range(RETRIES):
                curr_uuid = str(uuid.uuid1())

                shell_args = [
                    "blender",
                    "./sim/blender_envs/screw_sorter.blend",
                    "--python",
                    "./sim/scripts/run_sim.py",
                    "--",
                    str(input_folder_path / model / f"{model}.stl"),
                    str(output_folder_path),
                    curr_uuid,
                ]

                try:
                    logging.debug(" ".join(shell_args))
                    res = run(shell_args, stdout=PIPE, stderr=STDOUT)
                    break
                except TimeoutExpired:
                    logging.warning(f"Timeout {attempt=} with {model=} on {copy=} using {curr_uuid=}")
                except CalledProcessError as e:
                    logging.warning(f"Failed {attempt=} with {model=} on {copy=} using {curr_uuid=}: {e.output}")

if __name__ == "__main__":
    main()
