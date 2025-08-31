import imageio as iio
import json
import tkinter as tk
import os

from ..app import Project
from ..images import Slide
from ..pages import Starter, TargetProcessor
from ..utils import get_target_name
from .utils import (EXAMPLE_FOLDER, load_calibration_points, load_targets,
                    load_settings)

def load_project(page_name=None):
    """
    Load a saved project state based on the page name.

    Parameters:
    -----------
    page_name : str
        The name of the page whose project state is to be loaded.
    
    Returns:
    --------
    project : Project
        The loaded project object.
    """

    load_function_dict = {
        'Starter': load_starter,
        'SlideProcessor': load_slide_processor,
        'TargetProcessor': load_target_processor,
        'STalignRunner': load_stalign_runner,
        'SegmentationImporter': load_segmentation_importer,
        'VisuAlignRunner': load_visualign_runner,
        'RegionPicker': load_region_picker,
        'Exporter': load_exporter,
    }

    if page_name is None:
        project = load_exporter()
    elif page_name in load_function_dict:
        project = load_function_dict[page_name]()
    else:
        raise ValueError(f"Unknown page name: {page_name}")

    return project

def load_starter():
    """
    Load the project state for the Starter page. This function initializes
    and returns a new Project object.
    
    Returns:
    --------
    Project
        The initialized project object.
    """
    return Project()

def load_slide_processor():
    """
    Load the project state for the SlideProcessor page. This function builds
    upon the Starter page's project state. It loads the slides and atlases and
    creates a temporary project folder.
    
    Returns:
    --------
    Project
        The project object to be used in the SlideProcessor page.
    """
    project = load_starter()
    dummy_master = tk.Tk()
    dummy_starter = Starter(dummy_master, project)

    # load atlas
    print("Loading atlas", end='...')
    atlas_json_path = os.path.join(
        os.path.dirname(__file__), 
        EXAMPLE_FOLDER,
        'atlas.json'
    )
    with open(atlas_json_path, 'r') as f:
        atlas_name = json.load(f)
    dummy_starter.load_atlas_info(atlas_name)
    print("COMPLETE")

    # load slides
    print("Loading slides", end='...')
    dummy_starter.load_slides(os.path.join(
        os.path.dirname(__file__), 
        '..', 
        '..',
        'demo_images'
    ))
    print("COMPLETE")

    # create temporary project folder
    print("Creating temporary project folder", end='...')
    project.parent_folder = os.path.abspath(os.path.dirname(__file__))
    project.folder = os.path.join(
        project.parent_folder,
        "DART-temp"
    )
    os.makedirs(project.folder, exist_ok=True)
    print("COMPLETE")

    # clean up dummy master (will destroy dummy_starter as well)
    dummy_master.update()
    dummy_master.update_idletasks()
    dummy_master.destroy()

    return project

def load_target_processor():
    """
    Load the project state for the TargetProcessor page. This function builds
    upon the SlideProcessor page's project state. It loads the targets for the
    slides and the calibration points.
    """
    project = load_slide_processor()

    # load calibration points
    print("Loading calibration points", end='...')
    calib_coords_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        EXAMPLE_FOLDER,
        "calibration_points.json"
    )
    with open(calib_coords_path, 'r') as f:
        data = json.load(f)
        load_calibration_points(project, data)
    print("COMPLETE")

    # load targets
    print("Loading targets", end='...')
    target_coords_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        EXAMPLE_FOLDER,
        "target_coordinates.json"
    )
    with open(target_coords_path, 'r') as f:
        data = json.load(f)
        load_targets(project, data)
    print("COMPLETE")

    return project

def load_stalign_runner():
    """
    Load the project state for the STalignRunner page. This function builds
    upon the TargetProcessor page's project state. It loads the estimated
    affine transformations, landmarks, and STalign parameters for each target.
    """

    project = load_target_processor()
    dummy_master = tk.Tk()
    dummy_stalign_runner = TargetProcessor(dummy_master, project)

    for sn,slide in enumerate(project.slides):
        for tn,target in enumerate(slide.targets):
            # make target folder
            folder = os.path.join(
                project.folder, 
                get_target_name(sn, tn)
            )
            os.makedirs(folder, exist_ok=True)

            # load settings for each target
            settings_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
				EXAMPLE_FOLDER,
				get_target_name(sn, tn),
				"settings.json"
            )
            with open(settings_path, 'r') as f:
                data = json.load(f)
                load_settings(target, data)

            # compute img_estim for each target
            dummy_stalign_runner.update_img_estim(target)
        
        # estimate pix_dim for each slide
        slide.estimate_pix_dim()

    for slide in project.slides:
        for target in slide.targets:
            # compute seg_estim for each target
            dummy_stalign_runner.update_seg_estim(target)

    # clean up dummy master (will destroy dummy_stalign_runner as well)
    dummy_master.update()
    dummy_master.update_idletasks()
    dummy_master.destroy()

    return project

def load_segmentation_importer():
    """
    Load the project state for the SegmentationImporter page. The project
    state for this page is identical to that of the TargetProcessor state, so 
    this function simply calls `load_target_processor` and returns the project.
    In addition, since SegmentationImporter requires users to actually interact
    with the saved target images, this function saves the target images in the 
    project folder as DART typically does.
    """

    project = load_target_processor() # same project state as TargetProcessor

    # save the target images
    for si,slide in enumerate(project.slides):
        for ti,target in enumerate(slide.targets):
            path = os.path.join(
                project.folder,
                get_target_name(si, ti) + ".png"
            )
            iio.imsave(path, target.img_original)
    
    return project

def load_visualign_runner():
    project = load_stalign_runner()
    # TODO: implement
    return project

def load_region_picker():
    project = load_visualign_runner()
    # TODO: implement
    return project

def load_exporter():
    project = load_region_picker()
    # TODO: implement
    return project