import imageio as iio
import json
import numpy.testing as npt
import pytest
import shutil
import tkinter as tk
import os

from dart.pages import SlideProcessor
from dart.utils import get_target_name
from dart.test.load import load_slide_processor
from dart.test.utils import EXAMPLE_FOLDER, DummyEvent

@pytest.fixture(scope="module")
def project():
	loaded_project = load_slide_processor()
	yield loaded_project
	shutil.rmtree(loaded_project.folder)

@pytest.fixture
def slide_processor(master, project):
	return SlideProcessor(master, project)

@pytest.fixture
def activated_slide_processor(slide_processor):
	slide_processor.activate()
	return slide_processor

@pytest.fixture
def completed_slide_processor(activated_slide_processor):
    sp = activated_slide_processor

    # load calibration points
    calib_coords_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        EXAMPLE_FOLDER,
        "calibration_points.json"
    )
    with open(calib_coords_path, 'r') as f:
        data = json.load(f)
        load_calibration_points(sp, data)

    # load targets
    target_coords_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        EXAMPLE_FOLDER,
        "target_coordinates.json"
    )
    with open(target_coords_path, 'r') as f:
        data = json.load(f)
        load_targets(sp, data)

    return sp

def load_targets(sp, data):
    """
    Load targets using the provided data and the SlideProcessor interface.
    Activates rectangle annotation mode. Then, for each target, sets the 
    current slide to that slide and simulates a rectangle selection event on
    the target coordinates followed by a commit.
    
    Parameters
    ----------
    sp : SlideProcessor
        The SlideProcessor instance where targets will be added.
    data : list of dict
        A list of dictionaries containing slide numbers, target numbers, and
        their corresponding coordinates and shapes.
    """

    sp.activate_rect_mode()
    for target in data:
        sn = target['slide_index']
        x = target['x_offset']
        y = target['y_offset']
        t_shape = target['shape'][:2]

        sp.curr_slide_var.set(sn + 1)
        sp.refresh()

        click = DummyEvent(x, y)
        release = DummyEvent(x + t_shape[1], y + t_shape[0])
        sp.on_select(click, release)
        sp.commit()

def load_calibration_points(sp, data):
    """
    Load calibration points using the provided data and the SlideProcessor 
    interface. Activates point annotation mode, then sets the SlideProcessor 
    to point mode. For each slide, sets the current slide to that slide and for
    each calibration point, simulates a click event on the point and a click on
    the commit button.
    
    Parameters
    ----------
    sp : SlideProcessor
        The SlideProcessor instance where calibration points will be added.
    data : list of dict
        A list of dictionaries containing slide numbers and their corresponding
        calibration points.
    """

    sp.activate_point_mode()
    for slide in data:
        sn = slide['slide_index']
        sp.curr_slide_var.set(sn + 1)
        sp.refresh()
        for point in slide['points']:
            x = point[0]
            y = point[1]
            axes = sp.slide_viewer.axes[0]
            event = DummyEvent(x, y, inaxes=axes, button=1)
            sp.on_click(event)
            sp.commit()

def test_done(completed_slide_processor):
    sp = completed_slide_processor
    sp.done()
    
    # Check that calibration points are saved correctly
    cp_results_path = os.path.join(sp.project.folder, "calibration_points.json")
    assert os.path.exists(cp_results_path)
    cp_expected_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        EXAMPLE_FOLDER,
        "calibration_points.json"
    )
    with open(cp_results_path, 'r') as f_act, open(cp_expected_path, 'r') as f_exp:
        lines_act = f_act.readlines()
        lines_exp = f_exp.readlines()
        for la, le in zip(lines_act, lines_exp):
            assert la.strip() == le.strip()                   

    # Check that target images are saved correctly
    for si, slide in enumerate(sp.slides):
        for ti, target in enumerate(slide.targets):
            act_target_path = os.path.join(
                sp.project.folder, 
                get_target_name(si, ti) + ".png"
            )
            exp_target_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                EXAMPLE_FOLDER,
                get_target_name(si, ti) + ".png"
            )
            
            assert os.path.exists(act_target_path)
            saved_img_act = iio.imread(act_target_path)
            saved_img_exp = iio.imread(exp_target_path)
            npt.assert_array_equal(saved_img_act, saved_img_exp)

