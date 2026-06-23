import cv2
import numpy as np
import re
import json


def read_and_rectify_camera(camera_para_path):
    camera_matrix_l, dist_coeffs_l, camera_matrix_r, dist_coeffs_r, R, T = read_camera_para(camera_para_path)
    # frame_size = [1080, 1920]
    frame_size = [1920, 1080]
    R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
        camera_matrix_l, dist_coeffs_l,
        camera_matrix_r, dist_coeffs_r,
        frame_size, R, T, 
        flags=cv2.CALIB_ZERO_DISPARITY, alpha=-1
    )
    return R1, R2, P1, P2, Q, roi1, roi2


def read_camera_para(camera_para_path):
    if camera_para_path.endswith(".json"):
        return read_camera_para_json(camera_para_path)
    elif camera_para_path.endswith(".xml"):
        return read_camera_para_xml(camera_para_path)
    else:
        raise ValueError(f"Unknown camera para file type {camera_para_path}")


def read_camera_para_xml(camera_para_path):
    # 创建 FileStorage 对象
    fs = cv2.FileStorage(camera_para_path, cv2.FILE_STORAGE_READ)

    # 读取参数
    camera_matrix_l = fs.getNode('M1').mat()
    dist_coeffs_l = fs.getNode('D1').mat()
    camera_matrix_r = fs.getNode('M2').mat()
    dist_coeffs_r = fs.getNode('D2').mat()
    R = fs.getNode('R').mat()
    T = fs.getNode('T').mat()

    # 释放资源
    fs.release()

    return camera_matrix_l, dist_coeffs_l, camera_matrix_r, dist_coeffs_r, R, T

def read_camera_para_json(camera_para_path):
    with open(camera_para_path, "r") as f:
        carmera_para = json.load(f)
    
    camera_matrix_l = np.array(carmera_para["CameraParameters1"]["IntrinsicMatrix"]).astype(np.float64)
    camera_matrix_r = np.array(carmera_para["CameraParameters2"]["IntrinsicMatrix"]).astype(np.float64)
    
    dist_1 = carmera_para["CameraParameters1"]["RadialDistortion"]
    dist_2 = carmera_para["CameraParameters1"]["TangentialDistortion"]
    dist_coeffs_l = np.array([[dist_1[0], dist_1[1], dist_2[0], dist_2[1], dist_1[2]]]).astype(np.float64)

    dist_1 = carmera_para["CameraParameters2"]["RadialDistortion"]
    dist_2 = carmera_para["CameraParameters2"]["TangentialDistortion"]
    dist_coeffs_r = np.array([[dist_1[0], dist_1[1], dist_2[0], dist_2[1], dist_1[2]]]).astype(np.float64)
    
    R = np.array(carmera_para["RotationOfCamera2"]).astype(np.float64)
    T = np.array(carmera_para["TranslationOfCamera2"]).astype(np.float64)  # TODO: why can't delete???
    T = T[:, np.newaxis]

    return camera_matrix_l, dist_coeffs_l, camera_matrix_r, dist_coeffs_r, R, T


def read_pfm(file):
    file = open(file, 'rb')

    color = None
    width = None
    height = None
    scale = None
    endian = None

    header = file.readline().rstrip()
    if header.decode("ascii") == 'PF':
        color = True
    elif header.decode("ascii") == 'Pf':
        color = False
    else:
        raise Exception('Not a PFM file.')

    dim_match = re.match(r'^(\d+)\s(\d+)\s$', file.readline().decode("ascii"))
    if dim_match:
        width, height = list(map(int, dim_match.groups()))
    else:
        raise Exception('Malformed PFM header.')

    scale = float(file.readline().decode("ascii").rstrip())
    if scale < 0:  # little-endian
        endian = '<'
        scale = -scale
    else:
        endian = '>'  # big-endian

    data = np.fromfile(file, endian + 'f')
    shape = (height, width, 3) if color else (height, width)

    data = np.reshape(data, shape)
    data = np.flipud(data)
    return data, scale


if __name__ == "__main__":
    R1, R2, P1, P2, Q, roi1, roi2 = read_and_rectify_camera(r"W:\yrq\Data\toumai\calibration\EL82430_2305011\1114\camera_parameters.json")
    print(P1)
