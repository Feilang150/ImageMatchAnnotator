import numpy as np
import cv2
import json
import os
import sys


def load_kp(kp_path):
    with open(kp_path, "r") as f:
        kp = json.load(f)
    
    return kp


def get_common_kp(kp0, kp1):
    common_kp_ids = set(kp0.keys()) & set(kp1.keys())
    match_points = [(kp0[id], kp1[id]) for id in common_kp_ids]

    return match_points


root_dir = r"W:\yrq\Data\EndoAR\xinhua"
for case in sorted(os.listdir(root_dir)):
    case_dir = os.path.join(root_dir, case)
    if case=="backup":
        continue

    kp_dir = os.path.join(case_dir, "keypoints")

    with open(os.path.join(root_dir, case, "matches_backup.json"), "r") as f:
        old_match_data = json.load(f)
    # with open(os.path.join(case_dir, "matches_backup.json"), "w") as f:
    #     json.dump(old_match_data, f)

    match_data = []
    for match in old_match_data["matches"]:
        kp_path0 = os.path.join(kp_dir, match["name"][0]+".json")
        kp_path1 = os.path.join(kp_dir, match["name"][1]+".json")

        kp0 = load_kp(kp_path0)
        kp1 = load_kp(kp_path1)
        match_points = get_common_kp(kp0, kp1)

        match_data.append({
            "name": match["name"],
            "matches": match_points
        })

    with open(os.path.join(root_dir, case, "matches.json"), "w") as f:
        json.dump(match_data, f, indent=1)
