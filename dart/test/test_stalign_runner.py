import filecmp
import pytest
import shutil
import os

from ..pages import STalignRunner
from ..utils import get_target_name
from .load import load_stalign_runner
from .utils import EXAMPLE_FOLDER

@pytest.fixture(scope="module")
def project():
	loaded_project = load_stalign_runner()
	yield loaded_project
	shutil.rmtree(loaded_project.folder)

@pytest.fixture
def stalign_runner(master, project):
	return STalignRunner(master, project)

@pytest.fixture
def activated_stalign_runner(stalign_runner):
	stalign_runner.activate()
	return stalign_runner

@pytest.fixture
def completed_stalign_runner(activated_stalign_runner):
    sr = activated_stalign_runner
    sr.run()
    return sr

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

def test_done(completed_stalign_runner):
    sr = completed_stalign_runner
    sr.done()
    
    # check that each target has a transform and stalign segmentation
    for slide in sr.slides:
        for target in slide.targets:
            if target.stalign_params['iterations'] > 0:
                assert target.transform is not None
                assert 'stalign' in target.seg
    
    # check that results were saved correctly
    for sn,slide in enumerate(sr.slides):
        for tn,target in enumerate(slide.targets):
            act_folder_path = os.path.join(
                sr.project.folder,
                get_target_name(sn,tn)
            )
            exp_folder_path = os.path.join(
                os.path.dirname(__file__),
                EXAMPLE_FOLDER,
                get_target_name(sn,tn)
            )

            # check all stalign output files except for pickle files
            check_name = lambda name: 'stalign' in name and 'pkl' not in name
            files_to_check = [
                name
                for name in os.listdir(act_folder_path)
                if check_name(name)
            ]

            for filename in files_to_check:
                act_path = os.path.join(act_folder_path, filename)
                exp_path = os.path.join(exp_folder_path, filename)
                assert filecmp.cmp(act_path, exp_path, shallow=False)



