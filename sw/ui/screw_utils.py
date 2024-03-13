import uuid
from datetime import datetime
IMAGING_STATION_VERSION = 1.0
IMAGING_STATION_CONFIGURATION = "A1"

WIDTHS = {
    "1.85": "No. 1",
    "2.00": "M2",
    "2.18": "No. 2",
    "2.50": "M2.5",
    "2.51": "No. 3",
    "2.84": "No. 4",
    "3.00": "M3"
}

PITCHES = {
    "0.397": "64 threads per inch",
    "0.454": "56 threads per inch",
    "0.529": "48 threads per inch",
    "0.635": "40 threads per inch",
}

def create_label(filename_variables):
    """Creates json label for specific imaging run. any variables not entered into the GUI will be `None`."""

    if filename_variables["standard"].lower() == "metric":
        dia_units = "mm"
        len_units = "mm"
        pitch_units = "mm"
        ht_units = "mm"
        wd_units = "mm"
    elif filename_variables["standard"].lower() == "inch":
        # todo refactor dia_units when we introduce (larger) bolts that don't use ANSI
        dia_units = "ANSI #"
        len_units = "in"
        pitch_units = "TPI"
        ht_units = "in"
        wd_units = "in"
        
    label_json = {
        "uuid": str(uuid.uuid4()),
        "status": "ok",
        "world": "real",
        "platform_version": IMAGING_STATION_VERSION,
        "platform_configuration": IMAGING_STATION_CONFIGURATION,
        "time": datetime.now().strftime("%s"),
        "fastener_type": filename_variables["type"].lower(),
        "measurement_system": filename_variables["standard"].lower(),
        "attributes":{}
    }
    if label_json["fastener_type"] == "screw":
        attributes = {
            "length": str(filename_variables["length"]) + " " + len_units,
            "diameter": str(filename_variables["diameter"]) + " " + dia_units,
            "pitch": str(filename_variables["pitch"]) + " " + pitch_units,
            "head": filename_variables["head"].lower(),
            "drive": filename_variables["drive"].lower(),
            "direction": filename_variables["direction"].lower(),
            "finish": filename_variables["finish"].lower()
        }
    elif label_json["fastener_type"] == "washer":
        attributes = {
            "height": str(filename_variables["height"]) + " " + ht_units,
            "inner_diameter": str(filename_variables["inner_diameter"]) + " " + dia_units,
            "outer_diameter": str(filename_variables["outer_diameter"]) + " " + dia_units,
            "finish": filename_variables["finish"].lower(),
            "subtype": filename_variables["subtype"].lower()
        }
    elif label_json["fastener_type"] == "nut":
        attributes = {
            "width":str(filename_variables["width"]) + " " + wd_units,
            "height": str(filename_variables["height"]) + " " + ht_units,
            "diameter": str(filename_variables["diameter"]) + " " + dia_units,
            "pitch": str(filename_variables["pitch"]) + " " + pitch_units,
            "direction": filename_variables["direction"].lower(),
            "finish": filename_variables["finish"].lower(),
            "subtype": filename_variables["subtype"].lower()
        }
    label_json["attributes"] = attributes

    for k, v in label_json.items():
        if not v:
            print(f"{k} not selected properly")

    return label_json

def process_decoded_predictions(predictions):
    predictions = {feature: best_prediction(feature, preds) for feature, preds in predictions.items()}

    return predictions

def best_prediction(feature, feature_pred):
    max_p = 0
    best_choice = None
    for choice, p in feature_pred.items():
        p = float(p)
        if p > max_p:
            max_p = p
            best_choice = choice

    if feature == "length":
        best_choice = mm_or_inch(best_choice)

    if feature == "width":
        best_choice = WIDTHS[f"{float(best_choice):.2f}"]

    if feature == "pitch":
        if f"{float(best_choice):.3f}" in PITCHES:
            best_choice = PITCHES[f"{float(best_choice):.3f}"]
        else:
            best_choice = mm_or_inch(best_choice)

    return [best_choice, max_p]

def mm_or_inch(length, denom=16, eps=1e-6):
    length = float(length)
    length_inches = length / 25.4
    length_fractional = length_inches * denom

    if abs(length_fractional - round(length_fractional)) > eps:
        return f"{length:.2f}mm"
    
    while abs(length_fractional - round(length_fractional)) < eps:
        denom /= 2
        length_fractional /= 2
    
    denom *= 2
    length_fractional *= 2

    return f"{round(length_fractional)}/{int(denom)} in."

