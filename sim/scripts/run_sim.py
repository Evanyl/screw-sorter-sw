import bpy
import json
import math
import os
import random

def take_image(C, path, fastener, rotate):
    init_and_sim_fastener(C, fastener)

    #if not os.path.exists(path):
    #    os.makedirs(path)

    if rotate:
        full_rotation = 6.2831
        for i in range(13):
            angle = i * full_rotation / 12.0
            rotate.rotation_euler = (0, 0, angle)
            C.scene.render.filepath = f"{path}_{i * 30}.jpg"
            bpy.ops.render.render(write_still = True, use_viewport = True)
    else:
        C.scene.render.filepath = path
        bpy.ops.render.render(write_still = True, use_viewport = True)

def init_and_sim_fastener(C, fastener):
    mat = bpy.data.materials.get("metal2")
    fastener.data.materials.append(mat)

    x = random.randint(0, 2000) / 1000.0
    y = random.randint(0, 2000) / 1000.0

    x_angle = random.randint(0, 359)
    y_angle = math.radians(random.randint(0, 180))
    z_angle = random.randint(0, 359)

    fastener.location = (x, y, 2)
    fastener.rotation_euler = (x_angle, y_angle, z_angle)

    fastener.select_set(True)
    bpy.ops.rigidbody.objects_add(type='ACTIVE')
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
    frame = 1
    C.scene.frame_set(frame)
    for _ in range(130):
        frame += 1
        C.scene.frame_set(frame)

def run_sim(model_path, image_path, model_name, copies_to_take, label):
    for copy in range(copies_to_take):
        C = bpy.context
        bpy.ops.import_mesh.stl(filepath=model_path, global_scale=0.070, axis_up='X')
        fastener = bpy.data.objects[model_name]
        dir_name = f"{model_name}_{copy}" 
        label_path = os.path.join(image_path, dir_name, "label.json")
        dir_name += f"/{dir_name}"
        final_image_path = os.path.join(image_path, dir_name)

        rotate = bpy.data.objects.get('Empty')
        take_image(C, final_image_path, fastener, rotate)

        with open(label_path, 'w') as outfile:
            json.dump(label, outfile)

        bpy.ops.object.select_all(action='DESELECT')
        fastener.select_set(True)
        bpy.ops.object.delete()
    
def main():
    #types = ["M2x0_4mm", "M3x0_5mm"]
    types = ["M3_5x0_6mm", "M4x0_7mm", "I4x48", "I6x40", "I8x36"]
    #models = ['92095A453','92095A454','92095A104', '92095A179', '92095A181', '92095A182']
    models = [
        '92095A179',
        '92095A182',
        '92095A183',
        '92095A159',
        '92095A161',
        '92095A124',
        '92095A188',
        '92095A192',
        '92095A196',
        '92949A327',
        '92949A328',
        '92949A329',
        '92949A337',
        '92949A338',
        '92949A419',
        '92949A424',
        '92949A426',
        '91255A837',
    ]


    base_path_to_model = "/home/evanyl/ewa/school/screw-sorter-sw/sim/cads"
    base_path_to_image = "/home/evanyl/Dataset/sim_images/top_down"

    copies_to_take = 100

    for model_type in types:
        path_to_model = os.path.join(base_path_to_model, model_type)
        path_to_image = os.path.join(base_path_to_image, model_type)

        for model in [f for f in os.listdir(path_to_model) if not f.startswith(".") and f.endswith("stl")]:
            model_name = model.split(".")[0]
            if model_name not in models:
                print(f"Skipping {model_name}")
                continue
            model_path = os.path.join(path_to_model, model)
            image_path = os.path.join(path_to_image, model_name)
            with open(os.path.join(path_to_model, model_name + ".json"), 'r') as infile:
                label = json.load(infile)
            run_sim(model_path, image_path, model_name, copies_to_take, label)

if __name__ == "__main__":
    main()

