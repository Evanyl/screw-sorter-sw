import bpy
import cv2
import datetime
import json
import math
import numpy as np
import random
import sys
import time

from pathlib import Path

SIDEON_SCENE = "side-on"
TOPDOWN_SCENE = "top-down"
THRESH = 150

# Forgive my copy paste @gking, python 
# in blender paths are weird and these 
# are pretty lightweight
def _make_vector(vx, vy, x_center, y_center, x_centroid, y_centroid):
    """
    in:  - slope components from cv2.fitLine LS fit of contours vx and vy,
         - true midpoint coordinates of the contour x_center and y_center,
         - centroid coordinates of the contour x_centroid, y_centroid
    out: cartesian unit vector pointing in the direction of the screw head
    """
    vec = None
    m = -vy/vx

    if  ((m >= 1/2 and m >= 0) and (y_center >= y_centroid)) or \
        ((m < 1/2 and m >= 0) and (x_center <= x_centroid)):
        # Quadrant 1
        vec = (abs(vx), abs(vy))
    elif ((m <= -1/2 and m <= 0) and (y_center >= y_centroid)) or \
         ((m > -1/2 and m <= 0) and (x_center >= x_centroid)):
        # Quadrant 2
        vec = (-abs(vx), abs(vy))
    elif ((m <= 1/2 and m >= 0) and (x_center >= x_centroid)) or \
         ((m > 1/2 and m >= 0) and (y_center <= y_centroid)):
        # Quadrant 3
        vec = (-abs(vx), -abs(vy))
    elif ((m <= -1/2 and m <= 0) and (y_center <= y_centroid)) or \
         ((m > -1/2 and m <= 0) and (x_center <= x_centroid)):
        # Quadrant 4
        vec = (abs(vx), -abs(vy))
    return vec

def _correction_angle(vec):
    """
    in:  unit vector in the direction of screw head
    out: angle to rotate CW s/t unit vector is || to <1,0>
    """
    theta = np.arccos(np.dot([vec[0],vec[1]], [1,0]))*180/np.pi
    correction_theta = 0.0
    if (vec[0] >= 0 and vec[1] > 0):
        # Quadrant 1
        correction_theta = -theta
    elif (vec[0] < 0 and vec[1] >= 0):
       # Quadrant 2
       correction_theta = -theta
    elif (vec[0] <= 0 and vec[1] < 0):
       # Quadrant 3
       correction_theta = theta
    elif (vec[0] > 0 and vec[1] <= 0):
       # Quadrant 4
       correction_theta = theta
    return correction_theta

def _get_center(contours, x, y, vx, vy):
    """
    in:  - contour of screw from binarized image contours,
         - point on the fit line through the contour x and y,
         - slope components from cv2.fitLine LS fit of countour
    out: coordinates of the true mid-point of the contour (x,y)
    """
    err1 = sys.float_info.max
    err2 = sys.float_info.max
    p1 = (0,0)
    p2 = (0,0)
    m = -vy[0]/vx[0]
    p0_x = x[0]
    p0_y = y[0]

    for c in contours:
        p_x = c[0][0]
        p_y = c[0][1]
        if abs(-(p0_y-p_y)/(p0_x-p_x) - m) < err1 and p_x < p0_x:
            err1 = abs(-(p0_y-p_y)/(p0_x-p_x) - m)
            p1 = (p_x,p_y)
        if abs(-(p_y-p0_y)/(p_x-p0_x) - m) < err2 and p_x > p0_x:
            err2 = abs(-(p_y-p0_y)/(p_x-p0_x) - m)
            p2 = (p_x,p_y)

    return (int((p2[0] + p1[0])/2), int((p2[1] + p1[1])/2))

def get_correction_angle(read_fpath):
    """
    in:  path to raw image data to read read_fpath
    out: straightened and cropped binary image of shape 250x575
    """
    img = cv2.imread(read_fpath, cv2.IMREAD_UNCHANGED)
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
    _, img = cv2.threshold(img, THRESH, 255, cv2.THRESH_BINARY)

    contours,_ = cv2.findContours(img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    contours_sorted = sorted(contours, key=cv2.contourArea, reverse=True)

    # get data necessary for determining pose (centroid and true center)
    [vx,vy,x,y] = cv2.fitLine(contours_sorted[1], cv2.DIST_L2,0,0.01,0.01)
    M = cv2.moments(contours_sorted[1])
    x_centroid = int(M['m10']/M['m00'])
    y_centroid = int(M['m01']/M['m00'])
    x_center, y_center = _get_center(contours_sorted[1], x, y, vx, vy)

    # produce a unit vector in the direction of the screw head
    vec = _make_vector(vx[0], vy[0], x_center, y_center, x_centroid, y_centroid)
    return _correction_angle(vec)

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


def rotate_camera(C, fastener, z_angle):
    rotate = bpy.data.objects.get('side-on-rotation')
    rotate.rotation_euler = (0, 0, z_angle)

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

    # Top down
    top_down_image_path = output_path / f"0_{uuid}.png"

    C.window.scene = scenes[TOPDOWN_SCENE]
    play_scene(C)
    take_image(C, top_down_image_path)

    # Side
    correction_angle = get_correction_angle(str(top_down_image_path)) / -180 * np.pi
    #print(correction_angle)
    #input()
    side_image_path = output_path / f"1_{uuid}.png"
    
    C.window.scene = scenes[SIDEON_SCENE]
    play_scene(C)
    rotate_camera(C, fastener, correction_angle)

    take_image(C, side_image_path)

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

