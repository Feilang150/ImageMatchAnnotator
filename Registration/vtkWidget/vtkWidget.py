import os
import sys
sys.path.append(os.path.dirname(__file__))
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.numpy_support import vtk_to_numpy
import numpy as np
import cv2
import SimpleITK as sitk

from interector import CustomInteractorStyle
from Utils.utils import read_camera_para, read_and_rectify_camera
from Utils.vtkUtils import array2vtkTransform, vtkTransform2array


class VtkWidget(QVTKRenderWindowInteractor):
    def __init__(self, widget):
        super().__init__(widget)

        self.camera_para_path = r"Registration\EL82430_2305011.json"

        # do not read case_dir from global config at init — UI will provide it via LoadDirButton
        self.case_dir = None
        self.actor_dir = None

        self.actors = {}
        self.transform = vtk.vtkTransform()
        # self.init_transform = array2vtkTransform(np.array([[-0.987782, -0.115923, -0.104157, 116.611],
        #                                                 [0.0136365, -0.730077, 0.683228, -12.2349],
        #                                                 [-0.155244, 0.673459, 0.722738, 183.644],
        #                                                 [0, 0, 0, 1]]))
        self.init_transform = None

        self.init_renderwindow()

    def set_case_dir(self, case_dir: str):
        """Set the current case directory (provided by the UI) and load models from <case_dir>/models.
        This replaces reading `config["case_dir"]` at module init time.
        """
        if not case_dir:
            return

        self.case_dir = case_dir
        self.actor_dir = os.path.join(self.case_dir, "models")

    def run(self):
        self.set_camera_init()
        # self.set_actors(r"KidneyModel\Silicone")
        self.set_actors(self.actor_dir)

        self.renderWindow.Render()
        self.renderWindowInteractor.Start()
    
    def init_renderwindow(self):
        self.renderWindow = self.GetRenderWindow()
        self.renderWindow.SetSize(1920, 1080)
        self.renderWindow.SetNumberOfLayers(2)
        self.renderWindow.SetWindowName('EndoAR')

        # fg renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetLayer(1)
        self.renderWindow.AddRenderer(self.renderer)

        # bg renderer
        self.background_renderer = vtk.vtkRenderer()
        self.background_renderer.SetLayer(0)
        self.background_renderer.InteractiveOff()
        self.renderWindow.AddRenderer(self.background_renderer)

        # interector
        self.renderWindowInteractor = self.renderWindow.GetInteractor()
        self.renderWindowInteractor.SetRenderWindow(self.renderWindow)

        style = CustomInteractorStyle()
        style.SetDefaultRenderer(self.renderer)
        self.renderWindowInteractor.SetInteractorStyle(style)
    
    def set_camera_init(self):
        # read camera para
        R1, R2, P1, P2, Q, roi1, roi2 = read_and_rectify_camera(self.camera_para_path)
        cx = -Q[0,3]
        cy = -Q[1,3]
        f = Q[2,3]

        # camera
        camera = self.renderer.GetActiveCamera()

        camera.SetPosition(0, 0, 0)
        camera.SetFocalPoint(0, 0, 1)  # 0,0,1
        camera.SetViewUp(0,-1,0)
        camera.SetClippingRange([0.1, 1000])

        width, height = 1920, 1080
        wcx = -2*(cx - width/2) / width  # -2
        wcy = 2*(cy - height/2) / height
        camera.SetWindowCenter(wcx, wcy)

        view_angle = (2.0 * np.arctan2( height/2.0, f)) * 180 / np.pi
        camera.SetViewAngle(view_angle)

        # modelMatrix = vtkTransform2array(camera.GetModelTransformMatrix())
        # modelViewMatrix = vtkTransform2array(camera.GetModelViewTransformMatrix())
        viewMatrix = vtkTransform2array(camera.GetViewTransformMatrix())
        projMatrix = vtkTransform2array(camera.GetProjectionTransformMatrix(1920/1080, -1, 1))
        # compositeProjMatrix = vtkTransform2array(camera.GetCompositeProjectionTransformMatrix(1920/1080, -1, 1))
        denormalizeMatrix = np.array(
            [[1919/2, 0, 0, 1919/2],
            [0, 1079/2, 0, 1079/2],
            [0, 0, 1, 0],  
            [0, 0, 0, 1],]   
        )
        # print("camera model matrix: \n", modelMatrix, end="\n\n")
        print("camera view matrix: \n", viewMatrix, end="\n\n")
        # print("camera modelView matrix: \n", modelViewMatrix, end="\n\n")
        # print("camera proj matrix: \n", projMatrix, end="\n\n")
        # print("camera composite proj matrix: \n", compositeProjMatrix, end="\n\n")
        print("cameraMatrix (denormalize @ proj): \n", denormalizeMatrix@projMatrix, end="\n\n")

        # axes
        # axes = vtk.vtkAxesActor()
        # axes.SetTotalLength(1.0, 1.0, 1.0)
        # self.renderer.AddActor(axes) 

    def set_actors(self, actor_dir):
        self.renderer.RemoveAllViewProps()
        
        for case in os.listdir(actor_dir):
            casename = case[:-4]
            actor_path = os.path.join(actor_dir, case)

            if actor_path.endswith(".stl"):
                reader = vtk.vtkSTLReader()
            elif actor_path.endswith(".ply"):
                reader = vtk.vtkPLYReader()
            else:
                print("unknown model file type")

            reader.SetFileName(actor_path)
            reader.Update()

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.name = casename

            if self.init_transform is None:
                userTransform = self.move_actor_to_origin(actor)
            else:
                userTransform = self.init_transform

            actor.SetUserTransform(userTransform)
            actor.GetProperty().SetOpacity(0.33)
            if casename=="Kidney":
                actor.GetProperty().SetColor(1.0, 0.7333, 0.4667)  # sandy brown
            elif casename=="RenalArtery":
                actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # red
            elif casename=="RenalVein":
                actor.GetProperty().SetColor(0.0, 0.33, 1.0)  # slate blue
            elif casename=="Ureter":
                actor.GetProperty().SetColor(1.0, 1.0, 0.0)  # yellow
            elif casename.startswith("Tumor"):
                actor.GetProperty().SetColor(0.0, 0.667, 0.498)  # medium sea green
            self.renderer.AddActor(actor)
            self.actors[casename] = actor
        
        # axes
        axes_actor = vtk.vtkAxesActor()
        axes_actor.SetTotalLength(60, 60, 60)
        axes_actor.SetShaftTypeToCylinder()
        axes_actor.SetCylinderRadius(0.02)
        axes_actor.SetConeRadius(0.1)
        for captionActor in [axes_actor.GetXAxisCaptionActor2D(), axes_actor.GetYAxisCaptionActor2D(), axes_actor.GetZAxisCaptionActor2D()]:
            captionActor.GetTextActor().SetPosition(0, 32)
            captionActor.GetTextActor().SetTextScaleModeToNone()
            captionActor.GetCaptionTextProperty().SetFontSize(32)
        axes_actor.SetXAxisLabelText("Left")
        axes_actor.SetYAxisLabelText("Posterior")
        axes_actor.SetZAxisLabelText("Superior")
        axes_actor.name = "axes"

        self.renderer.AddActor(axes_actor)
        self.actors["axes"] = axes_actor

    def set_bg(self, img_path):
        image_reader = vtk.vtkPNGReader()
        image_reader.SetFileName(img_path)
        image_reader.Update()
        image_data = image_reader.GetOutput()

        # Create an image actor to display the image
        image_actor = vtk.vtkImageActor()
        image_actor.SetInputData(image_data)

        # Add actors to the renderers
        self.background_renderer.RemoveAllViewProps()
        self.background_renderer.AddActor(image_actor)

        # Set up the background camera to fill the renderer with the image
        origin = image_data.GetOrigin()
        spacing = image_data.GetSpacing()
        extent = image_data.GetExtent()

        camera = self.background_renderer.GetActiveCamera()
        camera.ParallelProjectionOn()

        xc = origin[0] + 0.5 * (extent[0] + extent[1]) * spacing[0]
        yc = origin[1] + 0.5 * (extent[2] + extent[3]) * spacing[1]
        # xd = (extent[1] - extent[0] + 1) * spacing[0]
        yd = (extent[3] - extent[2] + 1) * spacing[1]
        d = camera.GetDistance()
        camera.SetParallelScale(0.5 * yd)
        camera.SetFocalPoint(xc, yc, 0.0)
        camera.SetPosition(xc, yc, d)
    
    def get_cameraMatrix(self):
        camera = self.renderer.GetActiveCamera()

        projMatrix = vtkTransform2array(camera.GetProjectionTransformMatrix(1920/1080, -1, 1))
        denormalizeMatrix = np.array(
            [[1919/2, 0, 0, 1919/2],
            [0, 1079/2, 0, 1079/2],
            [0, 0, 1, 0],  
            [0, 0, 0, 1],]   
        )

        cameraMatrix = denormalizeMatrix@projMatrix
        cameraMatrix = cameraMatrix[:3, :3]
        cameraMatrix[2,2] = 1

        return cameraMatrix

    # TODO
    def set_camera(self, rotation_matrix, translation_vector):
        camera = self.renderer.GetActiveCamera()

        #  
        right = -rotation_matrix[0, 0:3]
        up = rotation_matrix[1, 0:3]
        direction = -rotation_matrix[2, 0:3]

        view_up = np.cross(direction, right)
        view_up /= np.linalg.norm(view_up)

        position = translation_vector[0,0] * right - translation_vector[1,0] * up + translation_vector[2,0] * direction

        focal_point = direction+position
        
        # 
        camera.SetPosition(position)
        camera.SetFocalPoint(focal_point)
        camera.SetViewUp(view_up)
        # self.renderer.ResetCameraClippingRange()

        # print("AR camera view matrix: \n", vtkTransform2array(camera.GetViewTransformMatrix()), end="\n\n")
    
    def window2img(self):
        windowToImageFilter = vtk.vtkWindowToImageFilter()
        windowToImageFilter.SetInput(self.renderWindow)
        windowToImageFilter.Update()

        imageData = windowToImageFilter.GetOutput()

        width, height, _ = imageData.GetDimensions()
        vtkArray = imageData.GetPointData().GetScalars()
        components = vtkArray.GetNumberOfComponents()

        array = vtk_to_numpy(vtkArray)
        array = array.reshape(height, width, components)

        # array = np.flip(array, axis=0)
        return array
    
    def add_point_actors(self):
        appendFilter = vtk.vtkAppendPolyData()

        sphere_positions =  [(7.590968443760822, -10.090658221982991, 130.86848516923104),
                            (16.19835673962256, -17.27029688842715, 129.08677909480565),
                            (24.769983407907585, -19.943927046703873, 126.59505699011874),
                            (37.328951620909265, -22.951870636042848, 125.85080868847847),
                            (51.597209443752426, -23.29636593120936, 127.36276017210791),
                            (61.9327840292092, -21.53426807093075, 130.0074824441034),
                            (37.400018991383476, -18.203080503902342, 124.5042146538403),
                            (14.14164472010198, -7.35626775891126, 128.76062271578712),
                            (32.640297751704296, -10.141467523095852, 124.5512788946106),
                            (43.55012309960556, -10.228573931429993, 124.79369007132397),
                            (57.81027875238303, -12.286257567613259, 127.2666595715439),
                            (63.432853245930616, -10.16302564616227, 128.2163149373422),
                            (71.44240501718694, -8.040287933839302, 130.84266642975672),
                            (5.580733592189183, 11.026573147884012, 144.68951844764288),
                            (10.705218490860396, 1.8292090390089903, 140.1958396043489),
                            (28.613092610945433, 2.521432245947395, 129.13483819065974),
                            (52.76893081164519, -1.1725354168960695, 129.05128262719734),
                            (67.49047280295392, 1.292910668725682, 131.81529934033935)]

        for position in sphere_positions:
            sphereSource = vtk.vtkSphereSource()
            sphereSource.SetRadius(2.0)  # 设置球体的半径
            sphereSource.SetThetaResolution(16)
            sphereSource.SetPhiResolution(16)

            transform = vtk.vtkTransform()
            transform.Translate(position)

            transformFilter = vtk.vtkTransformPolyDataFilter()
            transformFilter.SetTransform(transform)
            transformFilter.SetInputConnection(sphereSource.GetOutputPort())
            transformFilter.Update()

            appendFilter.AddInputData(transformFilter.GetOutput())

        appendFilter.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(appendFilter.GetOutputPort())

        self.points_actor = vtk.vtkActor()
        self.points_actor.SetMapper(mapper)
        self.points_actor.name = "points"

        self.points_actor.GetProperty().SetColor(0.0, 1.0, 0.0)

        self.renderer.AddActor(self.points_actor)
    
    def reset(self):
        # camera
        self.set_camera_init()

        # actor
        userTransform = self.init_transform

        for key in self.actors.keys():
            self.actors[key].SetUserTransform(userTransform)
    
    def compute_actor_center(self, actor):
        # 获取 PolyData
        polydata = actor.GetMapper().GetInput()
        
        center_filter = vtk.vtkCenterOfMass()
        center_filter.SetInputData(polydata)
        center_filter.SetUseScalarsAsWeights(False)
        center_filter.Update()
        
        center = center_filter.GetCenter()
        return center  # tuple (x, y, z)
    
    def move_actor_to_origin(self, actor):
        center = self.compute_actor_center(actor)

        # 设置反向平移 transform
        transform = vtk.vtkTransform()
        transform.Translate(-center[0], -center[1], -center[2])
        
        return transform


if __name__ == "__main__":
    vtkWidget = VtkWidget()
    vtkWidget.set_bg(r"W:\yrq\project_files\EndoAR\results\20241216154141\img_left_rectified.png")
    vtkWidget.set_fg(r"KidneyModel\Kidney.stl")
    vtkWidget.run()
