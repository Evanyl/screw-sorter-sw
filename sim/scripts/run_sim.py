import bpy
import datetime
import json
import math
import os
import random
import sys
import time

from pathlib import Path

SIDEON_SCENE = "side-on"
TOPDOWN_SCENE = "top-down"

def take_image(C, path):
    C.scene.render.filepath = str(path)
    print(f"Rendering {path}: {datetime.datetime.now().time()}")
    bpy.ops.render.render(write_still = True, use_viewport = True)
    print(f"Done rendering {path}: {datetime.datetime.now().time()}")

def init_cuda(C, scenes):
    # Set the device_type
    C.preferences.addons[
        "cycles"
    ].preferences.compute_device_type = "CUDA" # or "OPENCL"

    for scene in scenes.values():
        scene.render.engine = "CYCLES"
        scene.cycles.device = "GPU"

    # get_devices() to let Blender detects GPU device
    C.preferences.addons["cycles"].preferences.get_devices()
    print(C.preferences.addons["cycles"].preferences.compute_device_type)
    for d in C.preferences.addons["cycles"].preferences.devices:
        d["use"] = 1 # Using all devices, include GPU and CPU
        print(d["name"], d["use"])

def init_and_sim_fastener(C, fastener, scenes, height=60):
    init_cuda(C, scenes)

    for scene in scenes.values():
        scene.collection.objects.link(fastener)

    mat = bpy.data.materials.get("stainless-steel")
    fastener.data.materials.append(mat)

    x = random.randint(-2000, 2000) / 1000.0
    y = random.randint(-2000, 2000) / 1000.0

    x_angle = random.randint(-90, 90)
    y_angle = random.randint(-90, 90)
    z_angle = random.randint(0, 359)

    fastener.location = (x, y, 60)
    fastener.rotation_euler = (x_angle, y_angle, z_angle)


    fastener.select_set(True)
    bpy.ops.rigidbody.objects_add(type='ACTIVE')
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
    play_scene(C)

def play_scene(C, until_frame=250):
    frame = 0
    for _ in range(until_frame):
        C.scene.frame_set(frame)
        C.view_layer.update()
        frame += 1


def rotate_and_take_image(C, fastener, output_model_path, model_name):
    rotate = bpy.data.objects.get('Empty')
    full_rotation = 6.2831
    for i in range(9):
        angle = i * full_rotation / 9.0
        rotate.rotation_euler = (0, 0, angle)

        rotate_image_path = output_model_path / f"{model_name}_{i * 45}.jpg"
        take_image(C, rotate_image_path)

def run_sim(model_path, output_path, copies, label):
    output_path.mkdir(exist_ok=True)
    model_name = model_path.stem

    label_path = output_path / f"{model_name}.json"
    with open(label_path, 'w') as f:
        json.dump(label, f)

    for copy in range(copies):
        C = bpy.context
        scenes = {scene.name: scene for scene in bpy.data.scenes}
        bpy.ops.import_mesh.stl(filepath=str(model_path), axis_up='X')
        fastener = bpy.data.objects[model_name]

        init_and_sim_fastener(C, fastener, scenes)

        output_model_path = output_path / f"{model_name}_{copy}"
        output_model_path.mkdir(exist_ok=True)

        top_down_image_path = output_model_path / f"{model_name}_top.jpg"

        C.window.scene = scenes[TOPDOWN_SCENE]
        play_scene(C)
        take_image(C, top_down_image_path)

        C.window.scene = scenes[SIDEON_SCENE]
        play_scene(C)
        rotate_and_take_image(C, fastener, output_model_path, model_name)

        bpy.ops.object.select_all(action='DESELECT')
        fastener.select_set(True)
        bpy.ops.object.delete()

def main():
    """ 
        Run simulation in blender. Arguments are 'INPUT_FOLDER OUTPUT_FOLDER COPIES'
    """
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]  # get all args after "--"
    input_folder, output_folder, copies = argv

    input_folder_path = Path(input_folder)
    assert input_folder_path.exists(), f"{input_folder_path} does not exist"

    output_folder_path = Path(output_folder)
    assert output_folder_path.exists(), f"{output_folder_path} does not exist"

    cad_models = [d for d in os.listdir(input_folder_path) if os.path.isdir(input_folder_path / d)]
    print(f"Taking {copies=} of following models: {cad_models}")

    input_label_output_tuples = []
    for cad_model in cad_models:
        model_path = input_folder_path / cad_model / f"{cad_model}.stl"
        assert model_path.exists(), f"{model_path} does not exist. Should be formatted like output from 'scraper.py'"

        label_path = input_folder_path / cad_model / f"{cad_model}.json"
        assert label_path.exists(), f"{label_path} does not exist. Should be formatted like output from 'scraper.py'"
        output_path = output_folder_path / cad_model
        input_label_output_tuples.append((model_path, label_path, output_path))

    for model_path, label_path, output_path in input_label_output_tuples:
        with open(label_path, 'r') as f:
            label = json.load(f)
        run_sim(model_path, output_path, int(copies), label)

if __name__ == "__main__":
    main()

