import json
import os
import PIL
import shutil
import torch
import torchvision
import torchvision.transforms.functional as F

from utils import ModelHelper, DisplayHelper
"""
image_path = '/Users/evliu/evan/eng/ENPH459/sim/sample_images/92095A451_11_120.png'

model_helper = ModelHelper(model_path)
display_helper = DisplayHelper()

images, predictions = model_helper.predict_singular(image_path)
display_helper.display_single(images, predictions)

"""

big_labels = {
        "92095A287": {
            "thread_size": "M3",
            "thread_pitch": "0.5mm",
            "length": "3mm"
        },
        "92095A471": {
            "thread_size": "M3",
            "thread_pitch": "0.5mm",
            "length": "4mm"
        }
}

def gen_label(image_set_path, model_helper, display_helper, errors):
    image_set = image_set_path.split("/")[-1]
    image_path =  os.path.join(image_set_path, image_set + ".png")
    image, prediction = model_helper.predict_singular(image_path)
    trimmed_prediction = model_helper.decode_prediction([prediction])[0]
    if len(trimmed_prediction[0]) != 1:
        print(f"rut ro{image_set}")
        errors.append(image_set_path)
        return
        #raise Exception(f'{image_path} does not have 1 solid prediction. Could be more or less...')
    boxes_in_json = trimmed_prediction[0][0]

    label_path = os.path.join(image_set_path, 'label.json')
    if os.path.exists(label_path):
        with open(label_path, 'r') as json_file:
            label = json.load(json_file)
    else:
        ewa = image_set.split("_")[0]
        label = big_labels[ewa]

    label['bboxes'] = boxes_in_json.tolist()

    with open(label_path, 'w') as json_file:
        print("dumping")
        json.dump(label, json_file)
    #display_helper.display_single(image, trimmed_prediction)

def main():
    types = ["M3x0_5mm", "M3_5x0_6mm", "M4x0_7mm", "I4x48", "I6x40", "I8x36"]
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

    model_path = '/home/evanyl/ewa/school/screw-sorter-sw/ml/models/model_v1.pt'
    base_path_to_image = '/home/evanyl/Dataset/sim_images/top_down/'

    model_helper = ModelHelper(model_path)
    display_helper = DisplayHelper()

    errors = []
    to_process = []
    for model_type in types:
        path_to_image = os.path.join(base_path_to_image, model_type)

        for model in [f for f in os.listdir(path_to_image) if not f.startswith(".")]:
            if model not in models:
                continue
            image_folder_path = os.path.join(path_to_image, model)

            for image_set in [f for f in os.listdir(image_folder_path) if not f.startswith(".")]:
                image_set_path = os.path.join(image_folder_path, image_set)
                to_process.append(image_set_path)

    for i in range(len(to_process)):
        image_set_path = to_process[i]
        print(f"Processing {i + 1} /{len(to_process)}: {image_set_path}")
        gen_label(image_set_path, model_helper, display_helper, errors)

    with open('./errors.json', 'w+') as outfile:
        json.dump(errors, outfile)


if __name__ == "__main__":
    with open('errors.json', 'r') as infile:
        errors = json.load(infile)

    print(errors)
    print(len(errors))

    for error_path in errors:
        shutil.rmtree(error_path)

    #main()
