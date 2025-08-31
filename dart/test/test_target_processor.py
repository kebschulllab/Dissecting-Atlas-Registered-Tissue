import imageio as iio
import json
import numpy as np
import numpy.testing as npt
import os
import pytest
import shutil
import tkinter as tk

from dart.pages import TargetProcessor
from dart.utils import get_target_name
from dart.test.load import load_target_processor
from dart.test.utils import EXAMPLE_FOLDER, DummyEvent

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
                load_translation(tp, sn, tn, data['translation'])
                load_points(tp, sn, tn, data['landmarks'])
                load_params(tp, sn, tn, data['stalign_params'])
                
    return tp

def set_target(tp, slide_index, target_index):
    """
    Set the current target in the TargetProcessor using slide_index and
    target_index.

    Parameters
    ----------
    tp : TargetProcessor
        The TargetProcessor instance where the target will be set.
    slide_index : int
        The index of the slide containing the target.
    target_index : int
        The index of the target within the slide.
    """

    tp.curr_slide_var.set(slide_index + 1)
    tp.curr_target_var.set(target_index + 1)
    tp.update()

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

    # set current target
    set_target(tp, slide_index, target_index)

    # apply rotations
    tp.x_rotation_scale.set(rotations[2])
    tp.y_rotation_scale.set(rotations[1])
    tp.z_rotation_scale.set(rotations[0])
    tp.show_atlas()

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

    # set current target
    set_target(tp, slide_index, target_index)

    # apply translation
    tp.translation_scale.set(translations[0])
    tp.show_atlas()

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

    # set current target
    set_target(tp, slide_index, target_index)

    for atlas_point, target_point in zip(points['atlas'], points['target']):
        # simulate click on atlas point
        axes = tp.slice_viewer.axes[1]
        event = DummyEvent(atlas_point[1], atlas_point[0], inaxes=axes, button=1)
        tp.on_click(event)

        # simulate click on target point
        axes = tp.slice_viewer.axes[0]
        event = DummyEvent(target_point[1], target_point[0], inaxes=axes, button=1)
        tp.on_click(event)

        # simulate click on commit button
        tp.commit()

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

    # set current target
    set_target(tp, slide_index, target_index)
    
    # enter stalign parameters into entries
    for key, value in params.items():
        tp.param_vars[key].set(str(value))

    # save parameters
    tp.save_params()

def test_done(completed_target_processor):
    tp = completed_target_processor
    tp.done()

    for si, slide in enumerate(tp.project.slides):
        for ti, target in enumerate(slide.targets):
            # check estiamted pix_dim
            assert all(slide.pix_dim == target.pix_dim)

            # check that img_estim exists
            assert hasattr(target, 'img_estim')

            # check that seg_estim exists
            assert 'estimated' in target.seg

            # check that landmarks are consistent with count
            npt.assert_equal(
                len(target.landmarks['atlas']),
                target.num_landmarks
            )
            npt.assert_equal(
                len(target.landmarks['target']),
                target.num_landmarks
            )
    
            # check that target folders are created
            folder_name = get_target_name(si, ti)
            actual_path = os.path.join(
                tp.project.folder,
                folder_name
            )
            assert os.path.isdir(actual_path)

            expected_path = os.path.join(
                os.path.dirname(__file__),
                EXAMPLE_FOLDER,
                folder_name
            )

            # check settings json
            settings_path_act = os.path.join(
                actual_path,
                "settings.json"
            )
            settings_path_exp = os.path.join(
                expected_path,
                "settings.json"
            )
            with open(settings_path_act, 'r') as f_act:
                data_act = json.load(f_act)
            with open(settings_path_exp, 'r') as f_exp:
                data_exp = json.load(f_exp)
                
            assert data_act == data_exp

            # check estimated segmentation and outlines images
            assert result_image_equal(
                actual_path, 
                expected_path, 
                "estimated_segmentation.tif"
            )

            assert result_image_equal(
                actual_path,
                expected_path,
                "estimated_outlines.png"
            )

            assert result_image_equal(
                actual_path,
                expected_path,
                "estimated_outlines.tif"
            )

def result_image_equal(path_act, path_exp, filename):
    path_act = os.path.join(path_act, filename)
    path_exp = os.path.join(path_exp, filename)

    img_act = iio.imread(path_act)
    img_exp = iio.imread(path_exp)

    return np.all(img_act==img_exp)
