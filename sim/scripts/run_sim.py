import bpy
import datetime
import json
import math
import random
import sys
import time

from pathlib import Path

SIDEON_SCENE = "side-on"
TOPDOWN_SCENE = "top-down"

def take_image(C, path):
    C.scene.render.filepath = str(path)
    print(f"Rendering {path}: {datetime.datetime.now().time()}")
    C.scene.render.engine = "CYCLES"
    bpy.ops.render.render(write_still = True, use_viewport = True)

def init_cuda(C, scenes):
    # Set the device_type
    C.preferences.addons[
        "cycles"
    ].preferences.compute_device_type = "CUDA" # or "OPENCL"

    for scene in scenes.values():
        scene.cycles.device = "GPU"

    # get_devices() to let Blender detects GPU device
    C.preferences.addons["cycles"].preferences.get_devices()
    for d in C.preferences.addons["cycles"].preferences.devices:
        d["use"] = 1 # Using all devices, include GPU and CPU

def apply_texture(C, fastener):
    C.view_layer.objects.active = fastener
    # Toggle into Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')
    # Select the geometry
    bpy.ops.mesh.select_all(action='SELECT')
    # Call the smart project operator
    bpy.ops.uv.smart_project()
    # Toggle out of Edit Mode
    bpy.ops.object.mode_set(mode='OBJECT')

    mat = bpy.data.materials.get("stainless-steel")
    fastener.data.materials.append(mat)


def init_and_sim_fastener(C, fastener, scenes, height=60):
    init_cuda(C, scenes)

    for scene in scenes.values():
        scene.collection.objects.link(fastener)

    fastener.select_set(True)
    apply_texture(C, fastener)

    x = random.randint(-2000, 2000) / 1000.0
    y = random.randint(-2000, 2000) / 1000.0

    x_angle = math.radians(random.randint(0, 360))
    
    if random.randint(0, 1):
        y_angle = math.radians(random.randint(-30, 30))
    else:
        y_angle = math.radians(random.randint(150, 210))
    z_angle = math.radians(random.randint(0, 359))

    fastener.location = (x, y, 60)
    fastener.rotation_euler = (x_angle, y_angle, z_angle)

    bpy.ops.rigidbody.objects_add(type='ACTIVE')
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
    fastener.select_set(False)
    play_scene(C)

    post_rotation = fastener.matrix_world.to_euler()
    return post_rotation[-1]

def play_scene(C, until_frame=230):
    frame = 0
    for _ in range(until_frame):
        C.scene.frame_set(frame)
        C.view_layer.update()
        frame += 1


def rotate_and_take_image(C, fastener, output_model_path, model_name, z_angle=None):
    rotate = bpy.data.objects.get('side-on-rotation')
    if z_angle:
        rotate.rotation_euler = (0, 0, z_angle)

        rotate_image_path = output_model_path / f"{model_name}_side.jpg"
        take_image(C, rotate_image_path)

        return
    full_rotation = 6.2831
    for i in range(9):
        angle = i * full_rotation / 9.0
        rotate.rotation_euler = (0, 0, angle)

        rotate_image_path = output_model_path / f"{model_name}_{i * 45}.jpg"
        take_image(C, rotate_image_path)

def create_label(attributes, uuid):
    label = {
        "uuid": uuid,
        "world": "sim",
        "platform_version": "1.0",
        "platform_configuration": "0",
        "time": str(int(time.time())),
        "fastener_type": "screw",
        "measurement_system": attributes["system_of_measurement"],
        "topdown_included": True,
        "sideon_included": False,
        "number_sideon": 0,
        "attributes": attributes,
    }
    return label

def run_sim(model_path, output_path, attributes, uuid):
    output_path.mkdir(exist_ok=True)
    model_name = model_path.stem

    label_path = output_path / f"{uuid}.json"
    with open(label_path, 'w') as f:
        json.dump(create_label(attributes, uuid), f)

    C = bpy.context
    scenes = {scene.name: scene for scene in bpy.data.scenes}
    bpy.ops.import_mesh.stl(filepath=str(model_path), axis_up='X', axis_forward="-Y")
    fastener = bpy.data.objects[model_name]

    z_angle_of_fastener = init_and_sim_fastener(C, fastener, scenes)

    top_down_image_path = output_path / f"0_{uuid}.jpg"

    C.window.scene = scenes[TOPDOWN_SCENE]
    play_scene(C)
    take_image(C, top_down_image_path)

    
    C.window.scene = scenes[SIDEON_SCENE]
    play_scene(C)

    #z_angle_of_fastener += math.radians(random.randint(-15, 15))
    #rotate_and_take_image(C, fastener, output_model_path, model_name, z_angle=z_angle_of_fastener)

    print("Finished")
    bpy.data.objects.remove(fastener, do_unlink=True)

def main():
    """ 
        Run simulation in blender. Arguments are 'CAD_MODEL_PATH OUTPUT_FOLDER UUID'
    """
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]  # get all args after "--"
    cad_model, output_folder, uuid = argv

    cad_model_path = Path(cad_model)
    assert cad_model_path.exists(), f"{cad_model_path} does not exist"

    output_folder_path = Path(output_folder)
    assert output_folder_path.exists(), f"{output_folder_path} does not exist"

    print(f"Imaging {cad_model_path} with {uuid=}")
    
    label_path = cad_model_path.parent / f"{cad_model_path.stem}.json"
    output_path = output_folder_path / uuid

    with open(label_path, 'r') as f:
        attributes = json.load(f)
    run_sim(cad_model_path, output_path, attributes, uuid)

    bpy.ops.wm.quit_blender()

if __name__ == "__main__":
    main()

