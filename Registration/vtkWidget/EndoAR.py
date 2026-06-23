import vtk


class EndoAR:
    def __init__(self):
        self.actors = {}
        self.transform = vtk.vtkTransform()

        self.init_renderwindow()

    def run(self):
        self.renderWindow.Render()
        self.renderWindowInteractor.Start()
    
    def init_renderwindow(self):
        self.renderWindow = vtk.vtkRenderWindow()
        self.renderWindow.SetSize(1920, 1080)
        self.renderWindow.SetNumberOfLayers(2)
        self.renderWindow.SetWindowName('EndoAR')

        # interector
        self.renderWindowInteractor = vtk.vtkRenderWindowInteractor()
        self.renderWindowInteractor.SetRenderWindow(self.renderWindow)

        # fg renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetLayer(1)
        self.renderWindow.AddRenderer(self.renderer)

        # bg renderer
        self.background_renderer = vtk.vtkRenderer()
        self.background_renderer.SetLayer(0)
        self.background_renderer.InteractiveOff()
        self.renderWindow.AddRenderer(self.background_renderer)
    
    def set_fg(self, actor_path):
        stlReader = vtk.vtkSTLReader()
        stlReader.SetFileName(actor_path)
        stlReader.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(stlReader.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        self.renderer.RemoveAllViewProps()
        self.renderer.AddActor(actor)

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


if __name__ == "__main__":
    endoAR = EndoAR()
    endoAR.set_bg(r"W:\yrq\project_files\EndoAR\results\20241216154141\img_left_rectified.png")
    endoAR.set_fg(r"KidneyModel\Kidney.stl")
    endoAR.run()
