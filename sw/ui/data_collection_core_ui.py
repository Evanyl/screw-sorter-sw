from PyQt5 import QtCore, QtGui, QtWidgets
from python_qt_binding import loadUi
from collections import OrderedDict
from pathlib import Path

from ui.fractional_spinbox import CustomDoubleSpinBox

UI_PATH = Path("./sw/ui/data_collection.ui")
IMG_DIR_PATH = Path("./sw/ui/images")

COLORS_CONFIDENCE = {
    0.7: "#04a004",
    0.5: "#bfbf07",
    0.0: "#d80202"
}

class DataCollectionCoreUi(QtWidgets.QMainWindow):
    def __init__(self):
        super(DataCollectionCoreUi, self).__init__()
        loadUi(str(UI_PATH), self)

        # Dynamically create certain custom widgets and add it to layout (PyQtDesigner can't put it in natively)
        self.screw_length_imperial_double = CustomDoubleSpinBox()
        self.horizontalLayout_25.addWidget(self.screw_length_imperial_double)

        # The order of fields put in here determines the order in the filename.
        filename_variables = [
            "type", "standard", "subtype", "diameter", "pitch", "length", 
            "width", "inner_diameter", "outer_diameter", "height", "head", 
            "drive", "direction", "finish", ""
        ]
        self.filename_variables = OrderedDict()
        for filevar in filename_variables:
            self.filename_variables[filevar] = None
        self.setup_data_collection_ui()

        self.inference_features_map = {}
        self.setup_inference_results()

    def setup_inference_results(self):
        inference_features_to_locations = {
            "pitch": [368, 190],
            "width": [56, 224],
            "length": [464, 707],
            "drive": [1179, 134],
            "head": [735, 122],
        }

        for feature, coords in inference_features_to_locations.items():
            label = QtWidgets.QLabel(self.inference_results_img)
            label.setGeometry(*coords, 300, 50)
            label.setText(feature)
            label.setStyleSheet("font: 18pt")
            self.inference_features_map[feature] = label

    def display_inference_results(self, processed_preds, head=None, drive=None):
        if head and drive:
            img_name = f"{head}_{drive}.png"
            img_path = IMG_DIR_PATH / img_name

            if not img_path.exists():
                print(f"{str(img_path)} does not exist")

            self.inference_results_img.setPixmap(QtGui.QPixmap(str(img_path)))

        for feature, label in self.inference_features_map.items():
            pred, conf = processed_preds[feature]
            label.setText(f"{feature.title()}: {pred}")
            label.setStyleSheet(f"font: 18pt; font-weight: bold; {self.color_confidence(conf)}")

    def color_confidence(self, confidence):
        for conf_threshold, color in COLORS_CONFIDENCE.items():
            if confidence > conf_threshold:
                return f"color: {color}"

    def update_fastener_filename(self):
        current_name = ""
        for key, val in self.filename_variables.items():
            if val is not None:
                # attempt conversion to string
                try:
                    str_val = str(val)
                    # strip out slash from fraction
                    str_val = str_val.replace("/", "_")
                    current_name += str_val + "_"
                except TypeError:
                    pass
        self.fastener_filename.setText(current_name)

    def change_nut_standard_stack(self, pressed_button):
        # Update GUI appearance
        changed_index = False
        if pressed_button.text() == "Inch":
            if self.nut_standard_stack.currentIndex() != 1:
                self.nut_standard_stack.setCurrentIndex(1)
                changed_index = True
        elif pressed_button.text() == "Metric":
            if self.nut_standard_stack.currentIndex() != 2:
                self.nut_standard_stack.setCurrentIndex(2)
                changed_index = True

        self.filename_variables["standard"] = pressed_button.text()
       # Clear data fields of stack
        if changed_index:
            self.filename_variables["width"] = None
            self.filename_variables["height"] = None
            self.filename_variables["diameter"] = None
            self.filename_variables["pitch"] = None

        self.update_fastener_filename()

    def change_screw_standard_stack(self, pressed_button):
        # Update GUI appearance
        changed_index = False
        if pressed_button.text() == "Inch":
            if self.screw_standard_stack.currentIndex() != 1:
                self.screw_standard_stack.setCurrentIndex(1)
                changed_index = True
        elif pressed_button.text() == "Metric":
            if self.screw_standard_stack.currentIndex() != 2:
                self.screw_standard_stack.setCurrentIndex(2)
                changed_index = True
        
        self.filename_variables["standard"] = pressed_button.text()
        # Clear data fields of stack
        if changed_index:
            self.filename_variables["length"] = None
            self.filename_variables["diameter"] = None
            self.filename_variables["pitch"] = None

        self.update_fastener_filename()

    def change_washer_standard_stack(self, pressed_button):
        # Update GUI appearance
        changed_index = False
        if pressed_button.text() == "Inch":
            if self.washer_standard_stack.currentIndex() != 1:
                self.washer_standard_stack.setCurrentIndex(1)
                changed_index = True
        elif pressed_button.text() == "Metric":
            if self.washer_standard_stack.currentIndex() != 2:
                self.washer_standard_stack.setCurrentIndex(2)
                changed_index = True

        self.filename_variables["standard"] = pressed_button.text()
        # Clear data fields of stack
        if changed_index:
            self.filename_variables["inner_diameter"] = None
            self.filename_variables["outer_diameter"] = None
            self.filename_variables["height"] = None

        self.update_fastener_filename()

    def change_fastener_stack(self, pressed_button):
        if pressed_button.text() == "Screw":
            self.fastener_stack.setCurrentIndex(1)
        elif pressed_button.text() == "Washer":
            self.fastener_stack.setCurrentIndex(2)
        elif pressed_button.text() == "Nut":
            self.fastener_stack.setCurrentIndex(3)
        self.update_fastener_filename()

    def assign_height(self, height_text):
        self.filename_variables["height"] = height_text
        self.update_fastener_filename()

    def assign_width(self, width_text):
        self.filename_variables["width"] = width_text
        self.update_fastener_filename()

    def assign_drive(self, pressed_button):
        self.filename_variables["drive"] = pressed_button.text()
        self.update_fastener_filename()

    def assign_pitch(self, pressed_button):
        self.filename_variables["pitch"] = pressed_button.text()
        self.update_fastener_filename()

    def assign_direction(self, pressed_button):
        self.filename_variables["direction"] = pressed_button.text()
        self.update_fastener_filename()

    def assign_finish(self, pressed_button):
        self.filename_variables["finish"] = pressed_button.text()
        self.update_fastener_filename()

    def assign_inner_diameter(self, inner_diameter_text):
        self.filename_variables["inner_diameter"] = inner_diameter_text
        self.update_fastener_filename()

    def assign_outer_diameter(self, outer_diameter_text):
        self.filename_variables["outer_diameter"] = outer_diameter_text
        self.update_fastener_filename()

    def assign_fastener_type(self, pressed_button):
        self.filename_variables["type"] = pressed_button.text()
        self.update_fastener_filename()

    def assign_subtype(self, pressed_button):
        self.filename_variables["subtype"] = pressed_button.text()
        self.update_fastener_filename()

    def assign_diameter(self, pressed_button):
        self.filename_variables["diameter"] = pressed_button.text()
        self.update_fastener_filename()

    def assign_length(self, length_text):
        self.filename_variables["length"] = length_text
        self.update_fastener_filename()

    def assign_head(self, pressed_button):
        self.filename_variables["head"] = pressed_button.text()
        self.update_fastener_filename()

    def reset_filename_variables(self):
        # Reset variables for the next thread imaging suite
        for key in self.filename_variables:
            self.filename_variables[key] = None
        self.fastener_filename.setText("")
        # Unclick all buttons? No need?
        return

    def reset_filename_variables_when_changing_fastener(self, pressed_button):
        text = pressed_button.text()
        if self.filename_variables["type"] == text:
            # effect of clicking on the same button
            return
        else:
            self.reset_filename_variables()
            self.filename_variables["type"] = text
            self.fastener_filename.setText(text)

    def setup_data_collection_ui(self):
        self.FastenerTypeGroup.buttonClicked.connect(self.change_fastener_stack)
        self.FastenerTypeGroup.buttonClicked.connect(self.reset_filename_variables_when_changing_fastener)
        self.FastenerTypeGroup.buttonClicked.connect(self.assign_fastener_type)
        self.NutDiameterMetricGroup.buttonClicked.connect(self.assign_diameter)
        self.NutDiameterImperialGroup.buttonClicked.connect(self.assign_diameter)
        self.NutFinishGroup.buttonClicked.connect(self.assign_finish)
        self.NutPitchMetricGroup.buttonClicked.connect(self.assign_pitch)
        self.NutPitchImperialGroup.buttonClicked.connect(self.assign_pitch)
        self.NutStandardGroup.buttonClicked.connect(self.change_nut_standard_stack)
        self.NutDirectionGroup.buttonClicked.connect(self.assign_direction)
        self.NutTypeGroup.buttonClicked.connect(self.assign_subtype)
        self.nut_height_metric_double.textChanged.connect(self.assign_height)
        self.nut_width_metric_double.textChanged.connect(self.assign_width)
        self.nut_height_imperial_double.textChanged.connect(self.assign_height)
        self.nut_width_imperial_double.textChanged.connect(self.assign_width)

        self.ScrewDiameterMetricGroup.buttonClicked.connect(
            self.assign_diameter)
        self.ScrewDiameterImperialGroup.buttonClicked.connect(
            self.assign_diameter)
        self.ScrewDriveGroup.buttonClicked.connect(self.assign_drive)
        self.ScrewFinishGroup.buttonClicked.connect(self.assign_finish)
        self.ScrewHeadGroup.buttonClicked.connect(self.assign_head)
        self.screw_length_imperial_double.textChanged.connect(self.assign_length)
        self.screw_length_metric_double.textChanged.connect(self.assign_length)
        self.ScrewPitchMetricGroup.buttonClicked.connect(self.assign_pitch)
        self.ScrewPitchImperialGroup.buttonClicked.connect(self.assign_pitch)
        self.ScrewStandardGroup.buttonClicked.connect(
            self.change_screw_standard_stack)
        self.ScrewDirectionGroup.buttonClicked.connect(self.assign_direction)

        self.WasherFinishGroup.buttonClicked.connect(self.assign_finish)
        self.washer_inner_diameter_metric_double.textChanged.connect(self.assign_inner_diameter)
        self.washer_inner_diameter_imperial_double.textChanged.connect(self.assign_inner_diameter)
        self.washer_outer_diameter_metric_double.textChanged.connect(self.assign_outer_diameter)
        self.washer_outer_diameter_imperial_double.textChanged.connect(self.assign_outer_diameter)
        self.WasherStandardGroup.buttonClicked.connect(
            self.change_washer_standard_stack)
        self.washer_height_metric_double.textChanged.connect(self.assign_height)
        self.washer_height_imperial_double.textChanged.connect(self.assign_height)
        self.WasherTypeGroup.buttonClicked.connect(self.assign_subtype)

