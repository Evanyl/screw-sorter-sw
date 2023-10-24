import click
import json
import logging
import os
import shutil
import subprocess

from pathlib import Path

@click.command(help="Run blender sim")
@click.option("--input_folder_path", "input_folder_path", required=True, help="Input folder with donloaded CAD models")
@click.option("--output_folder_path", "output_folder_path", required=True, help="Output folder to put generated images")
@click.option("--copies", "copies", required=True, help="Number of copies for each fastener")
@click.option("--batch_size", "batch_size", required=True, default=10, help="Number of models to handle at a time")
@click.option("--curr_state_path", "curr_state_path", required=False, default=None, help="Path to curr_state.json from previous run")
def main(input_folder_path, output_folder_path, copies, batch_size, curr_state_path):
    logging.basicConfig(level=logging.INFO)

    input_folder_path = Path(input_folder_path)
    assert input_folder_path.exists(), f"{input_folder_path} does not exist"
    output_folder_path = Path(output_folder_path)
    assert output_folder_path.exists(), f"{output_folder_path} does not exist"

    remaining = []
    if curr_state_path:
        curr_state_path = Path(curr_state_path)
        assert curr_state_path.exists(), f"{curr_state_path} does not exist"
        with open(curr_state_path) as f:
            curr_state = json.load(f)

        to_delete = [output_folder_path / model_id for model_id in curr_state["to_convert"] + curr_state["failed"]]
        for delete_path in to_delete:
            if delete_path.exists():
                shutil.rmtree(delete_path)

        remaining = curr_state["remaining"] + curr_state["to_convert"] + curr_state["failed"]
    else:

        cad_models = set([d for d in os.listdir(input_folder_path) if os.path.isdir(input_folder_path / d)])
        existing = set([d for d in os.listdir(output_folder_path) if os.path.isdir(output_folder_path / d)])

        logging.info(f"{len(cad_models)} total")
        logging.info(f"{len(existing)} existing")
        logging.info(f"{len(cad_models - existing)} to convert")
        remaining = list(cad_models - existing)

    curr_state = {
        "remaining": remaining,
        "to_convert": [],
        "failed": [],
    }
    logging.info(f"{len(curr_state['remaining'])} remaining")

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
            logging.error(res.stderr)
            curr_state["failed"] = curr_state["to_convert"]

        logging.info(f"Finished with status code: {res.returncode}")
        curr_state["to_convert"] = []
        with open(curr_state_json_path, 'w') as f:
            json.dump(curr_state, f)

if __name__ == "__main__":
    main()
