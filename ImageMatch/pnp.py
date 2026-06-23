import os
import numpy as np
import cv2
import json

from utils import load_kp, load_world_points


def get_world_points(points, world_points):
    points_3d = []
    for i in range(points.shape[0]):
        point = points[i]

        x = int(round(point[0]))
        y = int(round(point[1]))

        points_3d.append(world_points[y, x])
    
    points_3d = np.array(points_3d)
    return points_3d


def get_2d_3d_points(points0, world_points0, points1):
    # points0[:,1] = 1079-points0[:,1]   # world points should already be flipped if vtk system
    # points1[:,1] = 1079-points1[:,1]
    
    points_3d0 = get_world_points(points0, world_points0)

    non_zero_mask = points_3d0[:,2]>0
    points0 = points0[non_zero_mask]
    points_3d0 = points_3d0[non_zero_mask]
    points1 = points1[non_zero_mask]

    return points0, points_3d0, points1


def pnp(points_3d0, points1, cameraMatrix, ransac=False):
    dist_coeffs = np.zeros((4, 1))

    points_3d0 = points_3d0.astype(np.float64)
    points1 = points1.astype(np.float64)
    
    if cameraMatrix[2,2]<0:  # vtk system
        points1[:,1] = 1079-points1[:,1]
        points1 = -points1

        initial_rvec = np.array([-np.pi, 0, 0], dtype=np.float32)  # [[1.0, 0, 0], [0, -1.0, 0], [0, 0, -1.0]]
    else:
        initial_rvec = np.array([0, 0, 0], dtype=np.float32)  # [[1.0, 0, 0], [0, -1.0, 0], [0, 0, -1.0]]
    initial_tvec = np.array([0.0, 0.0, 0.0], dtype=np.float32)

    if ransac:
        if cameraMatrix[2,2]<0:  # vtk system
            success, rvec, tvec, inliers = pnp_ransac_mine(points_3d0, points1, cameraMatrix)
        else:
            success, rvec, tvec, inliers = cv2.solvePnPRansac(points_3d0, points1, cameraMatrix, dist_coeffs,
                                                            rvec=initial_rvec, tvec=initial_tvec, useExtrinsicGuess=True,
                                                            reprojectionError = 50.0)
    else:
        success, rvec, tvec = cv2.solvePnP(points_3d0, points1, cameraMatrix, dist_coeffs,
                                                        rvec=initial_rvec, tvec=initial_tvec, useExtrinsicGuess=True)
        inliers = points_3d0.shape[0] # TODO: maybe should compute by error

    if success:
        rotation_matrix, _ = cv2.Rodrigues(rvec)

        reproject_points = cv2.projectPoints(points_3d0, rvec, tvec, cameraMatrix, dist_coeffs)[0].squeeze(1)
        error = reproject_points-points1
        if ransac:
            error = np.mean(np.sqrt(np.sum(np.square(error[inliers]), axis=1)))
        else:
            error = np.mean(np.sqrt(np.sum(np.square(error), axis=1)))

        # print("pnp points (select 3): \n", points1[:3], end="\n\n")
        # print("pnp reproject (select 3): \n", reproject_points[:3], end="\n\n")
        print("pnp reproject error: ", error)
        # print("pnp rotation: \n", rotation_matrix, end="\n\n")
        # print("pnp translation: \n", tvec, end="\n\n")

        return rotation_matrix, tvec, error, inliers.shape[0] if ransac else 0
    else:
        print("pnp failed")
        return None, None, None, 0

def pnp_ransac_mine(points_3d0, points1, cameraMatrix):
    # 过滤 z 太小的点
    points_3d0_filtered = []
    points1_filtered = []
    for i, pt_3d in enumerate(points_3d0):
        if pt_3d[2] > 2:
            points_3d0_filtered.append(pt_3d)
            points1_filtered.append(points1[i])

    # print("n matches after filter:", len(points_3d0_filtered))
    if len(points_3d0_filtered) < 4:
        print("not enough match points after filter")
        return False, None, None, None

    # PnP RANSAC
    object_points = np.array(points_3d0_filtered, dtype=np.float32)
    image_points = np.array(points1_filtered, dtype=np.float32)
    dist_coeffs = np.zeros((4, 1), dtype=np.float64)
    rvec_init = np.array([[-np.pi], [0.0], [0.0]], dtype=np.float64)
    tvec_init = np.zeros((3, 1), dtype=np.float64)

    success, rvec, tvec, inliers = cv2.solvePnPRansac(
        objectPoints=object_points,
        imagePoints=image_points,
        cameraMatrix=cameraMatrix,
        distCoeffs=dist_coeffs,
        rvec=rvec_init,
        tvec=tvec_init,
        useExtrinsicGuess=True,
        iterationsCount=100,
        reprojectionError=50.0,
        confidence=0.99,
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    if success:
        return True, rvec, tvec, inliers
    else:
        return False, None, None, None
