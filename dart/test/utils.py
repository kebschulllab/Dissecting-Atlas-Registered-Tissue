import imageio as iio
import pytest
import os
import tkinter as tk

from ..app import Project

EXAMPLE_FOLDER = "DART-expected"

def load_targets(project, data):
    """
    Load targets into the given project from the provided data.
    
    Parameters
    ----------
    project : Project
        The project instance where targets will be added.
    data : list of dict
        A list of dictionaries containing slide numbers, target numbers, and
        their corresponding coordinates and shapes.
    """
    for target in data:
        sn = target['slide_number']
        x = target['x_offset']
        y = target['y_offset']
        t_shape = target['shape'][:2]
        target_data = project.slides[sn].get_img()[y:y+t_shape[0], x:x+t_shape[1]]
        project.slides[sn].add_target(x, y, target_data)

def load_calibration_points(project, data):
    """
    Load calibration points into the given project from the provided data.
    
    Parameters
    ----------
    project : Project
        The project instance where calibration points will be added.
    data : list of dict
        A list of dictionaries containing slide numbers and their corresponding
        calibration points.
    """
    for slide in data:
        sn = slide['slide_number']
        for point in slide['points']:
            x = point[0]
            y = point[1]
            project.slides[sn].add_calibration_point([x, y])

