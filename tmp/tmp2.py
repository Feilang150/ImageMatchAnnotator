import os
import json
import shutil

# root_dir = r"W:\yrq\Data\EndoAR\xinhua"
root_dir = r"D:\yrq\Data\EndoAR\xinhua"

for case in sorted(os.listdir(root_dir)):
    # shutil.rmtree(os.path.join(root_dir, case, "keypoints"))
    # shutil.rmtree(os.path.join(root_dir, case, "kp_vis"))
    # os.remove(os.path.join(root_dir, case, "matches_backup.json"))
    if os.path.exists(os.path.join(root_dir, case, "test_match_vis")):
        shutil.rmtree(os.path.join(root_dir, case, "test_match_vis"))
