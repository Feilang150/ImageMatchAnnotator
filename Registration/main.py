import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QFileDialog, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QImage, QPixmap, qRgb, QMouseEvent
from PyQt5.QtCore import Qt, QRectF, QEvent
from Ui_win import Ui_MainWindow 

import numpy as np
import cv2
import vtk
import SimpleITK as sitk
import json


class MyMainWindow(QMainWindow,Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # connect Load Dir button to allow user to choose case directory
        self.LoadDirButton.clicked.connect(self.load_case_dir)
        
    def load_case_dir(self):
        # ask user to pick the case directory (contains 'img' and optional 'models')
        case_dir = QFileDialog.getExistingDirectory(self, "Select Case Directory", os.path.expanduser("~"))
        if not case_dir:
            return
        
        # tell vtk widget to use this case directory (loads models from case_dir/models)
        self.vtkWidget.set_case_dir(case_dir)
        self.vtkWidget.run()

        self.case_dir = case_dir
        frame_dir = os.path.join(self.case_dir, "img")
        self.save_dir = os.path.join(self.case_dir, "world_points")

        # load frames and configure scrollbar
        self.read_frames(frame_dir)

        self.frameScrollBar.setMinimum(0)
        self.frameScrollBar.setMaximum(len(self.img_left_paths)-1)
        self.frameScrollBar.valueChanged.connect(self.scrollFrame)
        self.scrollFrame(0)

        # add keyframe button
        self.cameraMatrix = self.vtkWidget.get_cameraMatrix()
        self.addKeyframeButton.clicked.connect(self.save_world_points)
    
    def read_frames(self, frame_dir):
        self.img_left_paths = None

        self.frame_names = os.listdir(frame_dir)
        self.img_left_paths = [os.path.join(frame_dir, x) for x in self.frame_names]

    def scrollFrame(self, i):
        self.i = i

        # img
        img_left_path = self.img_left_paths[i]
        self.img_left = cv2.imread(img_left_path)
        self.img_left = cv2.cvtColor(self.img_left, cv2.COLOR_BGR2RGB)
        
        # vtk img
        self.vtkWidget.set_bg(img_left_path)

        self.vtkWidget.renderWindow.Render()
    
    def save_world_points(self):
        # picker
        picker = vtk.vtkCellPicker()  # pick first touched point, so must be surface point!

        # get target actor
        actorCollection = self.vtkWidget.renderer.GetActors()
        actorCollection.InitTraversal()
        while True:
            targetActor = actorCollection.GetNextActor()
            if targetActor is None or targetActor.name=="Kidney":
                break
        
        # picklist
        picker.InitializePickList()
        picker.AddPickList(targetActor)
        picker.SetPickFromList(1)

        # cell locator
        dataset = targetActor.GetMapper().GetInput()
        poly_data = vtk.vtkPolyData.SafeDownCast(dataset)
        cell_locator = vtk.vtkStaticCellLocator()
        cell_locator.SetDataSet(poly_data)
        cell_locator.BuildLocator()
        picker.AddLocator(cell_locator)

        #  get points
        img = np.zeros([1080, 1920, 3])
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(1080)
        self.progressBar.setValue(0)
        for y in range(1080):
            for x in range(1920):
                # actually display coordinate
                picker.Pick(x, y, 0, self.vtkWidget.renderer)
                world_point = picker.GetPickPosition()

                picked_actor = picker.GetActor()
                # if picked_actor is not None:
                #     print(picker.GetActor().name, y, x, world_point)

                if picked_actor is not None and picker.GetActor().name == "Kidney":
                    img[y, x] = world_point  # TODO: maybe use dict?
            # 更新进度条
            self.progressBar.setValue(y+1)
            QApplication.processEvents()
        # save
        img = np.flip(img ,axis=0)
        save_name = self.frame_names[self.i].replace(".png", "")

        np.save(os.path.join(self.save_dir, f"{save_name}.npy"), img)
        cv2.imwrite(os.path.join(self.save_dir, f"{save_name}.png"), img)
        # 完成后重置进度条
        self.progressBar.setValue(0)
    
    def reset(self):
        self.vtkWidget.reset()
        self.vtkWidget.renderWindow.Render()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    myWin.show()
    sys.exit(app.exec_())
