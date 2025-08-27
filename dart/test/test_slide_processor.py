import imageio as iio
import numpy.testing as npt
import pytest
import shutil
import tkinter as tk
import os

from ..pages import SlideProcessor
from .load import load_slide_processor
from ..utils import get_target_name


@pytest.fixture(scope="module")
def project():
	loaded_project = load_slide_processor()
	yield loaded_project
	shutil.rmtree(loaded_project.folder)

@pytest.fixture(scope="module")
def master():
	root = tk.Tk()
	yield root
	root.destroy()

@pytest.fixture
def slide_processor(master, project):
	return SlideProcessor(master, project)

@pytest.fixture
def activated_slide_processor(slide_processor):
	slide_processor.activate()
	return slide_processor

def get_target_data(line):
    target_name, coords = line.strip().split(' : ')
    img = iio.imread(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        f"{target_name}.png"
    ))

    sn, tn = [int(s[-1]) for s in target_name.split('_')]
    x, y = map(int, coords.split())
    h, w = img.shape[:2]
    return sn, tn, x, y, h, w

def get_calibration_point_data(line):
    sn, coords = line.strip().split(' : ')
    sn = int(sn)
    x, y = map(int, coords.split())
    return sn, x, y

@pytest.fixture
def completed_slide_processor(activated_slide_processor):
    sp = activated_slide_processor

    # load targets
    target_coords_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "target_coordinates.txt"
    )
    with open(target_coords_path, 'r') as f:
        f.readline()
        for line in f.readlines():
            sn, _, x, y, h, w = get_target_data(line)
            data = sp.project.slides[sn-1].get_img()[y:y+h, x:x+w]

            sp.project.slides[sn-1].add_target(x, y, data)

    # load calibration points
    calib_coords_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "calibration_points.txt"
    )
    with open(calib_coords_path, 'r') as f:
        f.readline()
        for line in f.readlines():
            sn, x, y = get_calibration_point_data(line)
            sp.project.slides[sn-1].add_calibration_point([x, y])

    return sp

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

    class DummyEvent:
        def __init__(self, xdata, ydata):
            self.xdata = xdata
            self.ydata = ydata

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

    class DummyEvent:
        def __init__(self, xdata, ydata, inaxes, button):
            self.xdata = xdata
            self.ydata = ydata
            self.inaxes = True if inaxes else None
            self.button = button
    
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

	sp.curr_slide_var.set(numSlides)
	assert sp.get_index() == numSlides - 1

def test_done(completed_slide_processor):
    sp = completed_slide_processor
    sp.done()
    
    # Check that calibration points are saved correctly
    cp_results_path = os.path.join(sp.project.folder, "calibration_points.txt")
    assert os.path.exists(cp_results_path)
    cp_expected_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "calibration_points.txt"
    )
    with open(cp_results_path, 'r') as f_act, open(cp_expected_path, 'r') as f_exp:
        lines_act = f_act.readlines()
        lines_exp = f_exp.readlines()
        for la, le in zip(lines_act, lines_exp):
            assert la.strip() == le.strip()                   

    # Check that target images are saved correctly
    for si, slide in enumerate(sp.slides):
        for ti, target in enumerate(slide.targets):
            act_target_path = os.path.join(sp.project.folder, get_target_name(si, ti) + ".png")
            exp_target_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data",
                get_target_name(si, ti) + ".png"
            )
            
            assert os.path.exists(act_target_path)
            saved_img_act = iio.imread(act_target_path)
            saved_img_exp = iio.imread(exp_target_path)
            npt.assert_array_equal(saved_img_act, saved_img_exp)

