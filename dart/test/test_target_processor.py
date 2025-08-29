import json
import numpy.testing as npt
import os
import pytest
import shutil
import tkinter as tk

from ..pages import TargetProcessor
from ..utils import get_target_name
from .load import load_target_processor
from .utils import EXAMPLE_FOLDER

@pytest.fixture(scope="module")
def project():
	loaded_project = load_target_processor()
	yield loaded_project
	shutil.rmtree(loaded_project.folder)

@pytest.fixture
def target_processor(master, project):
	return TargetProcessor(master, project)

@pytest.fixture
def activated_target_processor(target_processor):
	target_processor.activate()
	return target_processor

@pytest.fixture
def completed_target_processor(activated_target_processor):
    tp = activated_target_processor

    # load settings for each target
    for sn,slide in enumerate(tp.project.slides):
        for tn,target in enumerate(slide.targets):
            settings_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
				EXAMPLE_FOLDER,
				get_target_name(sn, tn),
				"settings.json"
            )
            with open(settings_path, 'r') as f:
                data = json.load(f)

                load_rotation(tp, sn, tn, data['rotations'])
                load_translation(tp, sn, tn, data['translations'])
                load_points(tp, sn, tn, data['points'])
                load_params(tp, sn, tn, data['stalign_params'])
                
    return tp

def load_rotation(tp, slide_index, target_index, rotations):
    """
    Load rotations using the provided data and the TargetProcessor interface.
    Sets current target using slide_index and target_index. Then, applies the
    rotations to the target using the sliders in the TargetProcessor.

    Parameters
    ----------
    tp : TargetProcessor
        The TargetProcessor instance where rotations will be applied.
    slide_index : int
        The index of the slide containing the target.
    target_index : int
        The index of the target within the slide.
    rotations : list of float
        A list of rotation angles (in degrees) to be applied to the target.
    """
    return

def load_translation(tp, slide_index, target_index, translations):
    """
    Load translations using the provided data and the TargetProcessor interface.
    Sets current target using slide_index and target_index. Then, applies the
    translations to the target using the slider in the TargetProcessor.

    Parameters
    ----------
    tp : TargetProcessor
        The TargetProcessor instance where translations will be applied.
    slide_index : int
        The index of the slide containing the target.
    target_index : int
        The index of the target within the slide.
    translations : list of float
        A list of translation values to be applied to the target.
    """
    return

def load_points(tp, slide_index, target_index, points):
    """
    Load points using the provided data and the TargetProcessor interface.
    Sets current target using slide_index and target_index. Then, for each
    pair of atlas and target points, simulates clicks at their location then
    clicks the commit button.

    Parameters
    ----------
    tp : TargetProcessor
        The TargetProcessor instance where points will be applied.
    slide_index : int
        The index of the slide containing the target.
    target_index : int
        The index of the target within the slide.
    points : dict
        A dictionary containing lists of atlas and target points.
    """
    return

def load_params(tp, slide_index, target_index, params):
    """
    Load stalign parameters using the provided data and the TargetProcessor
    interface. Sets current target using slide_index and target_index. Then,
    applies the stalign parameters to the target using the entries in the
    TargetProcessor and the "Save" button.

    Parameters
    ----------
    tp : TargetProcessor
        The TargetProcessor instance where stalign parameters will be applied.
    slide_index : int
        The index of the slide containing the target.
    target_index : int
        The index of the target within the slide.
    params : dict
        A dictionary containing stalign parameters.
    """
    return