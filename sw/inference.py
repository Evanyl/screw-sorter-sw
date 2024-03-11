import numpy as np
import time
import json
import cv2
import tflite_runtime.interpreter as tflite

from pathlib import Path

class Predictor:

    def __init__(self, model_path: Path, decoder_path: Path):
        self.interpreter = tflite.Interpreter(model_path=str(model_path))
        self.interpreter.allocate_tensors()

        input_details = self.interpreter.get_input_details()
        output_details = self.interpreter.get_output_details()

        output_details.sort(key=lambda x: x['name'])

        self.input_shape = input_details[0]['shape']
        self.input_index = input_details[0]['index']
        self.output_indexes = [output_detail['index'] \
                               for output_detail in output_details]
        self.predictions = None
        with open(decoder_path) as f:
            self.decoder = json.load(f)

    ############################################################################
    #                 P U B L I C    C L A S S    M E T H O D S                #
    ############################################################################ 

    def predict(self, file_path):
        input_img = cv2.imread(str(file_path))
        input_img = np.float32(input_img / 127.5 - 1)
        input_img = np.expand_dims(input_img, axis=0)

        self.interpreter.set_tensor(self.input_index, input_img)
        self.interpreter.invoke()

        self.predictions = [self.interpreter.get_tensor(i)[0] \
                            for i in self.output_indexes]

    def decode(self, preds):
        decoded = {}
        for i, feature in enumerate(self.decoder["features"]):
            decoded[feature] = {str(self.decoder[f'{feature}_id'][str(j)]): 
                                str(v) for j, v in enumerate(preds[i])}
        return decoded
