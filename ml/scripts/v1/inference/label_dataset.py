import os
import PIL
import torch
import torchvision
import torchvision.transforms.functional as F

from utils import ModelHelper, DisplayHelper

model_path = '/Users/evliu/evan/eng/ENPH459/ml/models/model_v1.pt'
image_path = '/Users/evliu/evan/eng/ENPH459/sim/sample_images/92095A451_11_120.png'

model_helper = ModelHelper(model_path)
display_helper = DisplayHelper()

images, predictions = model_helper.predict_singular(image_path)
display_helper.display_single(images, predictions)

