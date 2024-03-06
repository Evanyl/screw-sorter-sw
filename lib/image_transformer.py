import os
import cv2
import numpy  as np
import json
from pathlib import Path
import re
import sys

INCH_TO_MM = 25.4

num2inchwidth = [
    0.060, # No.0
    0.073, # No.1
    0.086, # No.2
    0.099, # No.3
    0.112, # No.4
    0.125, # No.5 
    0.138, # No.6
]

THRESH = 150

# helpers for label generation

def _imp_to_metric(s):
    """
    in: imperial string
    out: float
    """

    s = s.split('"')[0]

    if "/" in s:
        return _sfrac2float(s) * INCH_TO_MM
    else:
        return float(s) * INCH_TO_MM

def _sfrac2float(s):
    """
    in:  str fraction "{num}/{denom}"
    out: float
    """
    nums = s.split("/")
    return int(nums[0]) / int(nums[1])

def _processMetric(label):
    """
    in:  metric label dict
    out: unified metric label dict
    """
    w = float(label["thread_size"].split("M")[-1])
    l = float(label["length"].split("mm")[0])
    p = float(label["thread_pitch"].split("mm")[0])
    # return {"width": w, "length": l, "pitch": p, "metric": True}
    return {"length": l, "pitch": p, "metric": True}

def _processImperial(label):
    """
    in:  imperial label dict
    out: unified metric label dict
    """
    thread_size = label["thread_size"].split("-")
    # w = num2inchwidth[int(thread_size[0])]*INCH_TO_MM
    l = _sfrac2float(label["length"].split('"')[0])*INCH_TO_MM
    p = 1.0/int(thread_size[1])*INCH_TO_MM
    # return {"width": w, "length": l, "pitch": p, "metric": False}
    return {"length": l, "pitch": p, "metric": True}

# temporary private functions to handle difference between real and sim labels
# TODO: Rectify this
def _processMetric_real(label):
    """
    in:  metric label from the imaging station
    out: unified metric label dict
    """
    w = float(label["attributes"]["diameter"].split(" ")[0][1:])
    l = float(label["attributes"]["length"].split(" ")[0])
    p = float(label["attributes"]["pitch"].split(" ")[0])
    h = label["attributes"]["head"].lower()
    d = label["attributes"]["drive"].lower()
    system = label["measurement_system"].lower()
    world = label["world"].lower()
    id = label["uuid"]
    return {
        "length": l,
        "width":  w,
        "pitch":  p,
        "head":   h,
        "drive":  d,
        "system": system,
        "world":  world,
        "id":     id
    }
    

def _processMetric_sim(label):
    """
    in:  metric label from the simulation
    out: unified metric label dict
    """
    w = float(label["attributes"]["diameter"])
    l = float(label["attributes"]["length"].split("mm")[0])
    p = float(label["attributes"]["pitch"].split("mm")[0])
    h = label["attributes"]["head"].lower()
    d = label["attributes"]["drive"].lower()
    finish = label["attributes"]["finish"].lower()
    head_diameter = float(label["attributes"]["head_diameter"].split("mm")[0])
    system = label["measurement_system"].lower()
    world = label["world"].lower()
    id = label["uuid"]
    return {
        "length": l,
        "width":  w,
        "pitch":  p,
        "head":   h,
        "drive":  d,
        "finish": finish,
        "head_diameter": head_diameter,
        "system": system,
        "world":  world,
        "id":     id
    }

def _processImperial_real(label):
    """
    in:  imperial label from the imaging station
    out: unified metric label dict
    """
    w = num2inchwidth[int(label["attributes"]["diameter"].split(" ")[0])]*INCH_TO_MM
    l = _sfrac2float(label["attributes"]["length"].split(" ")[0])*INCH_TO_MM
    p = 1.0/int(label["attributes"]["pitch"].split(" ")[0])*INCH_TO_MM
    h = label["attributes"]["head"].lower()
    d = label["attributes"]["drive"].lower()
    system = label["measurement_system"].lower()
    world = label["world"].lower()
    id = label["uuid"]
    return {
        "length": l,
        "width":  w,
        "pitch":  p,
        "head":   h,
        "drive":  d,
        "system": system,
        "world":  world,
        "id":     id
    }

def _processImperial_sim(label):
    """
    in:  imperial label from the simulation
    out: unified metric label dict
    """
    thread_size = label["attributes"]["thread_size"].split("-")
    w = num2inchwidth[int(thread_size[0])]*INCH_TO_MM
    l = _sfrac2float(label["attributes"]["length"].split('"')[0])*INCH_TO_MM
    p = 1.0/int(thread_size[-1])*INCH_TO_MM
    h = label["attributes"]["head"].lower()
    d = label["attributes"]["drive"].lower()
    finish = label["attributes"]["finish"].lower()
    head_diameter = _imp_to_metric(label["attributes"]["head_diameter"])
    system = label["measurement_system"].lower()
    world = label["world"].lower()
    id = label["uuid"]
    return {
        "length": l,
        "width":  w,
        "pitch":  p,
        "head":   h,
        "drive":  d,
        "finish": finish,
        "head_diameter": head_diameter,
        "system": system,
        "world":  world,
        "id":     id
    }

# helpers for pose estimation and screw normalization
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

# rename this to _make_vector or something
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

def _straighten(image, center, theta):
    """
    in:  - full sized top-down image img, 
         - center point of image center, 
         - angle to rotate CW theta
    out: CW rotated image about center by angle theta (deg)
    """
    shape = (image.shape[1], image.shape[0])
    matrix = cv2.getRotationMatrix2D(center=center, angle=theta, scale=1)
    return cv2.warpAffine(src=image, M=matrix, dsize=shape)

def _crop(img):
    """
    in:  full-sized straightened image using _straighten
    out: tight cropped image using cv2.minAreaRect
    """
    contours,_ = cv2.findContours(img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    contours_sorted = sorted(contours, key=cv2.contourArea, reverse=True)
    x,y,w,h = cv2.boundingRect(contours_sorted[1])
    return img[y:y+h,x:x+w]

def _pad(img, desired_shape):
    """
    in:  - tight cropped image using _crop img,
         - shape to pad to with white border desired_shape
    out: padded image
    """
    out = None
    if img.shape[0] < desired_shape[0] and img.shape[1] < desired_shape[1]:
        equal_hpad = not (desired_shape[1] - img.shape[1]) % 2
        equal_vpad = not (desired_shape[0] - img.shape[0]) % 2
        if equal_hpad and equal_vpad:
            dx = int((desired_shape[1] - img.shape[1]) / 2)
            dy = int((desired_shape[0] - img.shape[0]) / 2)
            out = cv2.copyMakeBorder(img, dy, dy, dx, dx,
                                        cv2.BORDER_CONSTANT,
                                        value=[255, 255, 255])
        elif equal_hpad and not equal_vpad:
            dx = int((desired_shape[1] - img.shape[1]) / 2)
            dy = int((desired_shape[0] - img.shape[0]) // 2)
            out = cv2.copyMakeBorder(img, dy, dy+1, dx,
                                        dx, cv2.BORDER_CONSTANT,
                                        value=[255, 255, 255])
        elif not equal_hpad and equal_vpad:
            dx = int((desired_shape[1] - img.shape[1]) // 2)
            dy = int((desired_shape[0] - img.shape[0]) / 2)
            out = cv2.copyMakeBorder(img, dy, dy, dx, dx+1, cv2.BORDER_CONSTANT,
                                        value=[255, 255, 255])
        elif not equal_hpad and not equal_vpad:
            dx = int((desired_shape[1] - img.shape[1]) // 2)
            dy = int((desired_shape[0] - img.shape[0]) // 2)
            out = cv2.copyMakeBorder(img, dy, dy+1, dx, dx+1, 
                                     cv2.BORDER_CONSTANT, value=[255, 255, 255])
    else:
       raise Exception("Bounding Box Error: size of subject exceeds 250x575")
    return out

def get_correction_angle(read_fpath):
    """
    in:  path to raw image data to read read_fpath
    out: straightened and cropped binary image of shape 250x575
    """
    img = cv2.imread(str(read_fpath), cv2.IMREAD_UNCHANGED)
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

def transform_top_image(read_fpath):
    """
    in:  path to raw image data to read read_fpath
    out: straightened and cropped binary image of shape 250x575
    """
    img = cv2.imread(str(read_fpath), cv2.IMREAD_UNCHANGED)
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
    correction_theta = _correction_angle(vec)

    # correct the image so the head is facing to the right
    img = _straighten(img, (x_center, y_center), correction_theta)
    img = _crop(img)
    img = _pad(img, [400, 800]) # 250 575

    return img

def transform_side_image(read_fpath, crop_w=800/2, crop_h=800/2, top_plane_y=1600, bot_plane_y=2450, left_plane_x=1696, right_plane_x=3800): # 5496
    """
    in:  path to raw image data to read read_fpath
    out: cropped image of shape 800x800
    """

    img = cv2.imread(str(read_fpath), cv2.IMREAD_UNCHANGED)
    img = img[top_plane_y:bot_plane_y, left_plane_x:right_plane_x]
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)

    blur = cv2.blur(img,(13,13), 0)
    _, img = cv2.threshold(blur, 130, 255, cv2.THRESH_BINARY_INV)

    contours,_ = cv2.findContours(img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    main_contour = sorted(contours, key=cv2.contourArea, reverse=True)[0]

    M = cv2.moments(main_contour)
    cX = int(M["m10"] / M["m00"]) + left_plane_x
    cY = int(M["m01"] / M["m00"]) + top_plane_y

    img = cv2.imread(str(read_fpath), cv2.IMREAD_COLOR)
    img = img[int(cY-crop_h):int(cY+crop_h), int(cX-crop_w):int(cX+crop_w)]

    return img

def transform_images(write_dpath, read_dpath):
    """
    in:  - path to directory to write processed data to write_dpath
         - path to directory upholding directory to read from read_dpath
    out: flat directory structure holding processed data
    """
    write_dpath = Path(write_dpath)
    read_dpath = Path(read_dpath)
    count = 0
    home = os.getcwd()
    os.chdir(read_dpath)
    data_directories = [f for f in os.listdir(read_dpath) \
                        if os.path.isdir(f) and not f.startswith(".")]
    for data_directory in data_directories:
        os.chdir(data_directory)
        metadata_file = [f for f in os.listdir() if f.endswith(".json")][0]
        label = {}

        with open(metadata_file) as mf:
            metadata = json.load(mf)
            if re.match("real", metadata["world"]):
                if re.match("inch", metadata["measurement_system"].lower()):
                    label = _processImperial_real(metadata)
                else:
                    label = _processMetric_real(metadata)
            else:
                if re.match("inch", metadata["measurement_system"].lower()):
                    label = _processImperial_sim(metadata)
                else:
                    label = _processMetric_sim(metadata)

        image_files = [f for f in os.listdir() if not f.endswith(".json")]
        top_img = None
        side_img = None
        name = None
        print(data_directory)
        for image_file in image_files:
            image_num = image_file.split("_")[0]
            name = "screw_{s}_{u}_{w}_{l}_{p}_{d}_{h}_{n}"\
                    .format(s=label["world"]           ,
                            u=label["system"]          ,
                            w=round(label["width"],  3),
                            l=round(label["length"], 3), 
                            p=round(label["pitch"],  3),
                            d=label["drive"]           ,
                            h=label["head"]            ,
                            n=label["id"])

            if image_num == "0":
                top_img = transform_top_image(image_file)
            elif image_num == "1":
                side_img = transform_side_image(image_file)

        curr_write_dir = write_dpath / name
        os.makedirs(curr_write_dir, exist_ok=True)

        #cv2.imwrite(str(curr_write_dir / f"1_{name}.png"), side_img)
        top_img = np.stack((top_img,)*3, axis=-1)
        img_concat = np.concatenate([top_img, side_img], axis=0)

        cv2.imwrite(str(curr_write_dir / f"{name}.png"), img_concat)
        with open(curr_write_dir / f"{name}.json", "w") as f:
            json.dump(label, f)

        count += 1
        print(f"Processed Image{count}")
        os.chdir(read_dpath)
    os.chdir(home)
