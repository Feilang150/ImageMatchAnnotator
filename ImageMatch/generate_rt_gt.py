import os
import cv2
import numpy as np
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils import load_kp, load_world_points
from pnp import pnp, get_2d_3d_points


def get_common_kp(kp0, kp1):
    common_kp_ids = sorted(set(kp0.keys()) & set(kp1.keys()))
    points0 = np.array([kp0[id] for id in common_kp_ids])
    points1 = np.array([kp1[id] for id in common_kp_ids])

    return points0, points1


def run(match_data, case_dir):
    # with open(os.path.join(case_dir, "matches.json"), "r") as f:
    #     data = json.load(f)
    
    camera_matrix = np.array([[1851.44452, 0.0, -719.177052], 
                              [0.0, 1850.69413, -553.656241], 
                              [0.0, 0.0, -1.00010001]])

    errors = []
    pnp_gt = {
        "camera_matrix": camera_matrix.tolist(),
        "pnp_gt": []
    }
    for i in range(len(match_data)):
        name0 = match_data[i]["name"][0]
        name1 = match_data[i]["name"][1]

        # load
        points = np.array(match_data[i]["matches"])  # (n, 2, 2)
        points0 = points[:, 0, :]  # (n, 2)
        points1 = points[:, 1, :]  # (n, 2)

        world_points0_path = os.path.join(case_dir, "world_points", name0+".npy")
        world_points0 = load_world_points(world_points0_path)

        # pnp
        points0, points_3d0, points1 = get_2d_3d_points(points0, world_points0, points1)
        r,t,error,n_inliers = pnp(points_3d0, points1, camera_matrix, ransac=False)

        pnp_gt["pnp_gt"].append(
            {
                "name": [name0, name1],
                "R": r.tolist(),
                "T": t.tolist(),
                "pnp_error": error,
                "n_inliers": n_inliers
            }
        )
        errors.append(error)
    
    pnp_gt["pnp_error"] = np.mean(np.mean(errors))
    
    # with open(os.path.join(case_dir, "pnp_gt.json"), "w") as f:
    #     json.dump(pnp_gt, f, indent=1)

    return pnp_gt


if __name__ == "__main__":
    case_dir = r"D:\xinhua\903_0830hong"
    run(case_dir)
