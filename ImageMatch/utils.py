import os
import cv2
import numpy as np
import json


def read_camera_para(camera_para_path):
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


def load_kp(kp_path):
    with open(kp_path, "r") as f:
        kp = json.load(f)
    
    return kp


def load_world_points(world_points_path):
    world_points = np.load(world_points_path)
    return world_points
