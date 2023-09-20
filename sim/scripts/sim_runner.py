import click
import json
import logging
import os
import subprocess

from pathlib import Path

@click.command(help="Run blender sim")
@click.option("--input_folder_path", "input_folder_path", required=True, help="Input folder with donloaded CAD models")
@click.option("--output_folder_path", "output_folder_path", required=True, help="Output folder to put generated images")
@click.option("--copies", "copies", required=True, help="Number of copies for each fastener")
@click.option("--batch_size", "batch_size", required=True, default=10, help="Number of models to handle at a time")
def main(input_folder_path, output_folder_path, copies, batch_size):
    logging.basicConfig(level=logging.INFO)

    input_folder_path = Path(input_folder_path)
    assert input_folder_path.exists(), f"{input_folder_path} does not exist"
    output_folder_path = Path(output_folder_path)
    assert output_folder_path.exists(), f"{output_folder_path} does not exist"

    cad_models = set([d for d in os.listdir(input_folder_path) if os.path.isdir(input_folder_path / d)])
    existing = set([d for d in os.listdir(output_folder_path) if os.path.isdir(output_folder_path / d)])

    logging.info(f"{len(cad_models)} total")
    logging.info(f"{len(existing)} existing")
    logging.info(f"{len(cad_models - existing)} to convert")

    curr_state = {
        "remaining": list(cad_models),
        "to_convert": [],
        "failed": [],
    }
    curr_state_json_path = output_folder_path / "curr_state.json"

    while curr_state["remaining"]:
        to_pop = min(batch_size, len(curr_state["remaining"]))

        curr_state["to_convert"] = curr_state["remaining"][:to_pop]
        curr_state["remaining"] = curr_state["remaining"][to_pop:]

        with open(curr_state_json_path, 'w') as f:
            json.dump(curr_state, f)

        res = subprocess.run([
            "blender",
            "./sim/blender_envs/screw_sorter.blend",
            "--python",
            "./sim/scripts/run_sim.py",
            "--",
            str(input_folder_path),
            str(output_folder_path),
            str(curr_state_json_path),
            str(copies),
        ])

        if res.returncode:
            logging.error(f"Errored out, adding to failed field in {str(curr_state_json_path)}")
            curr_state["failed"] = curr_state["to_convert"]

        logging.info(f"Finished with status code: {res.returncode}")
        curr_state["to_convert"] = []

if __name__ == "__main__":
    main()
