import vtk

class CustomInteractorStyle(vtk.vtkInteractorStyleTrackballActor):
    def __init__(self, parent=None):
        super(CustomInteractorStyle, self).__init__()
        self.AddObserver("LeftButtonPressEvent", self.OnLeftButtonDown)
        self.AddObserver("LeftButtonReleaseEvent", self.OnLeftButtonUp)
        self.AddObserver("RightButtonPressEvent", self.OnRightButtonDown)
        self.AddObserver("RightButtonReleaseEvent", self.OnRightButtonUp)
        self.AddObserver("MiddleButtonPressEvent", self.OnMiddleButtonDown)
        self.AddObserver("MiddleButtonReleaseEvent", self.OnMiddleButtonUp)
        self.AddObserver("MouseMoveEvent", self.OnMouseMove)
        self.AddObserver("MouseWheelForwardEvent", self.OnMouseWheelForward)
        self.AddObserver("MouseWheelBackwardEvent", self.OnMouseWheelBackward)

        self.left_button_pressed = False
        self.right_button_pressed = False
        self.middle_button_pressed = False
        self.last_position = None

    def OnLeftButtonDown(self, obj, event):
        self.left_button_pressed = True
        self.last_position = self.GetInteractor().GetEventPosition()
        return

    def OnLeftButtonUp(self, obj, event):
        self.left_button_pressed = False
        return

    def OnRightButtonDown(self, obj, event):
        self.right_button_pressed = True
        self.last_position = self.GetInteractor().GetEventPosition()
        return

    def OnRightButtonUp(self, obj, event):
        self.right_button_pressed = False
        return

    def OnMiddleButtonDown(self, obj, event):
        self.middle_button_pressed = True
        self.last_position = self.GetInteractor().GetEventPosition()
        return

    def OnMiddleButtonUp(self, obj, event):
        self.middle_button_pressed = False
        return

    def OnMouseMove(self, obj, event):
        if self.last_position is None:
            return

        current_position = self.GetInteractor().GetEventPosition()
        dx = current_position[0] - self.last_position[0]
        dy = current_position[1] - self.last_position[1]

        # 
        actors = self.GetDefaultRenderer().GetActors()
        
        center = None
        actors.InitTraversal()
        for i in range(actors.GetNumberOfItems()):
            actor = actors.GetNextActor()

            try:  # axes actor has no attribute "name"
                if actor.name == "Kidney":
                    center = self.calculate_actor_centroid(actor)
            except:
                pass

        transform = vtk.vtkTransform()
        transform.PostMultiply()

        if self.left_button_pressed:
            # Rotate around x and y axes
            transform.Translate(-center[0], -center[1], -center[2])
            transform.RotateY(dx)
            transform.RotateX(-dy)
            transform.Translate(center[0], center[1], center[2])
        elif self.right_button_pressed:
            # Rotate around z axis
            transform.Translate(-center[0], -center[1], -center[2])
            transform.RotateZ(dx)
            transform.Translate(center[0], center[1], center[2])
        elif self.middle_button_pressed:
            # Translate in x and y
            transform.Translate(dx * 1, -dy * 1, 0)
        else:
            # just move. no press
            return
        
        actors.InitTraversal()
        for i in range(actors.GetNumberOfItems()):
            actor = actors.GetNextActor()

            actor_transform = actor.GetUserTransform()
            if actor_transform is None:
                actor_transform = vtk.vtkTransform()
            actor_transform.PostMultiply()
            actor_transform.Concatenate(transform)

            actor.SetUserTransform(actor_transform)
            # print(actor_transform)
        
        # 
        self.GetInteractor().GetRenderWindow().Render()

        self.last_position = current_position
        return

    def OnMouseWheelForward(self, obj, event):
        transform = vtk.vtkTransform()
        transform.PostMultiply()

        transform.Translate(0, 0, -2)

        actors = self.GetDefaultRenderer().GetActors()
        actors.InitTraversal()
        for i in range(actors.GetNumberOfItems()):
            actor = actors.GetNextActor()

            actor_transform = actor.GetUserTransform()
            if actor_transform is None:
                actor_transform = vtk.vtkTransform()
            actor_transform.PostMultiply()
            actor_transform.Concatenate(transform)

            actor.SetUserTransform(actor_transform)

        self.GetInteractor().GetRenderWindow().Render()
        return

    def OnMouseWheelBackward(self, obj, event):
        transform = vtk.vtkTransform()
        transform.PostMultiply()

        transform.Translate(0, 0, 2)

        actors = self.GetDefaultRenderer().GetActors()
        actors.InitTraversal()
        for i in range(actors.GetNumberOfItems()):
            actor = actors.GetNextActor()

            actor_transform = actor.GetUserTransform()
            if actor_transform is None:
                actor_transform = vtk.vtkTransform()
            actor_transform.PostMultiply()
            actor_transform.Concatenate(transform)

            actor.SetUserTransform(actor_transform)

        self.GetInteractor().GetRenderWindow().Render()
        return
    
    def calculate_actor_centroid(self, actor):
        mapper = actor.GetMapper()
        if not mapper:
            raise ValueError("Actor does not have a valid mapper.")
        
        input_data = mapper.GetInput()
        if not input_data:
            raise ValueError("Mapper does not have valid input data.")
        
        points = input_data.GetPoints()
        if not points:
            raise ValueError("Input data does not have valid points.")

        num_points = points.GetNumberOfPoints()
        centroid = [0.0, 0.0, 0.0]
        
        for i in range(num_points):
            p = points.GetPoint(i)
            centroid[0] += p[0]
            centroid[1] += p[1]
            centroid[2] += p[2]

        centroid[0] /= num_points
        centroid[1] /= num_points
        centroid[2] /= num_points

        userTransform = actor.GetUserTransform();
        if userTransform is not None:
            centroid = userTransform.TransformPoint(centroid);
        # print(centroid)

        return centroid
    
