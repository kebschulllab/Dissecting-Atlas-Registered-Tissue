import imageio as iio
import json
import numpy.testing as npt
import pytest
import shutil
import tkinter as tk
import os

from ..pages import SlideProcessor
from .load import load_slide_processor
from ..utils import get_target_name
from .utils import EXAMPLE_FOLDER, DummyEvent

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
            event = DummyEvent(x, y, inaxes=True, button=1)
            sp.on_click(event)
            sp.commit()

def test_init(slide_processor):
	assert hasattr(slide_processor, "header")
	assert hasattr(slide_processor, "currSlide")
	assert hasattr(slide_processor, "newPointX")
	assert hasattr(slide_processor, "newTargetX")
	assert hasattr(slide_processor, "slice_selector")
	assert hasattr(slide_processor, "menu_frame")
	assert hasattr(slide_processor, "annotation_mode")
	assert hasattr(slide_processor, "menu_buttons_frame")
	assert hasattr(slide_processor, "slide_nav_combo")
	assert hasattr(slide_processor, "slides_frame")

def test_activate(activated_slide_processor):
	sp = activated_slide_processor
	# Should set up initial state and call super().activate()
	assert sp.annotation_mode.get() in ["point", "rect"]
	assert sp.currSlide is not None
	
def test_refresh(activated_slide_processor):
    sp = activated_slide_processor
    sp.refresh()
    index = sp.get_index()
    assert sp.currSlide == sp.slides[index]
	
    numSlides = len(sp.slides)
    sp.curr_slide_var.set(numSlides+1)
    with pytest.raises(IndexError):
        sp.refresh()

@pytest.mark.parametrize("equal_click_release", [True, False])
def test_on_select(activated_slide_processor, equal_click_release):
    sp = activated_slide_processor
    img = sp.currSlide.get_img()

    if equal_click_release:
        # Case 1: click and release at the same spot
        click = DummyEvent(10, 20)
        release = DummyEvent(10, 20)
        sp.on_select(click, release)
        assert sp.newTargetX == -1
        assert sp.newTargetY == -1
        assert sp.newTargetData is None
    else:
        # Case 2: click and release at different spots (rectangle selection)
        click = DummyEvent(5, 5)
        release = DummyEvent(15, 25)
        sp.on_select(click, release)
        assert sp.newTargetX == 5
        assert sp.newTargetY == 5
        assert sp.newTargetData.shape[:2] == (20, 10)
        expected = img[5:25, 5:15]
        npt.assert_array_equal(sp.newTargetData, expected)

@pytest.mark.parametrize("inaxes", [True, False])
@pytest.mark.parametrize("button", [1, 2])
def test_on_click(activated_slide_processor, inaxes, button):
    sp = activated_slide_processor
    
    event = DummyEvent(10, 20, inaxes, button)
    sp.on_click(event)
    if inaxes and button == 1:
        assert sp.newPointX == 10
        assert sp.newPointY == 20
    else:
        assert sp.newPointX == -1
        assert sp.newPointY == -1

def test_get_index(activated_slide_processor):
	sp = activated_slide_processor
	numSlides = len(sp.slides)

	sp.curr_slide_var.set(1)
	assert sp.get_index() == 0

	sp.curr_slide_var.set(numSlides+1)
	assert sp.get_index() == numSlides

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

