import bpy
import os
import random

def take_image(C, path, fastener, rotate):
    init_and_sim_fastener(C, fastener)

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
    y_angle = random.randint(0, 359)
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

def run_sim(model_path, image_path, model_name, copies_to_take):
    for copy in range(copies_to_take):
        C = bpy.context
        bpy.ops.import_mesh.stl(filepath=model_path, global_scale=0.070, axis_up='X')
        fastener = bpy.data.objects[model_name]
        dir_name = f"{model_name}_{copy}" 
        dir_name += f"/{dir_name}"
        final_image_path = os.path.join(image_path, dir_name)

        rotate = bpy.data.objects.get('Empty')
        take_image(C, final_image_path, fastener, rotate)

        bpy.ops.object.select_all(action='DESELECT')
        fastener.select_set(True)
        bpy.ops.object.delete()
    
def main():
    types = ["M2x0_4mm", "M3x0_5mm"]

    base_path_to_model = "/Users/evliu/evan/eng/ENPH459/sim/cads/"
    #base_path_to_image = "/Volumes/EVANYL/sim_images/"
    base_path_to_image = "/Users/evliu/evan/eng/ENPH459/sim/sample_images"

    copies_to_take = 100

    for model_type in types:
        path_to_model = os.path.join(base_path_to_model, model_type)
        path_to_image = os.path.join(base_path_to_image, model_type)

        for model in [f for f in os.listdir(path_to_model) if not f.startswith(".")]:
            model_name = model.split(".")[0]
            model_path = os.path.join(path_to_model, model)
            image_path = os.path.join(path_to_image, model_name)

            run_sim(model_path, image_path, model_name, copies_to_take)

if __name__ == "__main__":
    main()

