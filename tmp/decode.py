import os
import time

root_dir = r"D:\Projects\ImageMatchAnnotator\tmp"
file_name = r"tmp.py"

file_path = os.path.join(root_dir, file_name)
file_path1 = os.path.join(root_dir, file_name+".xml")
file_path2 = os.path.join(root_dir, "1"+file_name+".xml")
file_path3 = os.path.join(root_dir, "1"+file_name)

os.rename(file_path, file_path1)
# time.sleep(2)
os.rename(file_path1, file_path2)
# time.sleep(2)
# os.rename(file_path2, file_path3)
# time.sleep(2)
# os.rename(file_path3, file_path)
