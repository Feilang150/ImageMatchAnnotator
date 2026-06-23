import vtk
import numpy as np


def array2vtkTransform(array, return_matrix=False):
    vtk_matrix = vtk.vtkMatrix4x4()
    for i in range(4):
        for j in range(4):
            vtk_matrix.SetElement(i, j, array[i][j])

    # 
    if return_matrix:
        return vtk_matrix
    else:
        vtk_transform = vtk.vtkTransform()
        vtk_transform.SetMatrix(vtk_matrix)
        return vtk_transform

def vtkTransform2array(vtk_transform):
    np_matrix = np.zeros((4, 4))

    for i in range(4):
        for j in range(4):
            np_matrix[i, j] = vtk_transform.GetElement(i, j)
    
    return np_matrix
