import json
import tkinter as tk
import os

from ..app import Project
from ..images import Slide
from ..pages import Starter
from .utils import get_calibration_point_data, get_target_data

def load_project(page_name):
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

    if page_name in load_function_dict:
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
        'data',
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
    os.mkdir(project.folder)
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
    cp_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "calibration_points.txt"
    )
    with open(cp_path, 'r') as f:
        f.readline()
        for line in f.readlines():
            sn, x, y = get_calibration_point_data(line)
            project.slides[sn-1].add_calibration_point([x, y])
    print("COMPLETE")

    # load targets
    print("Loading targets", end='...')
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
            data = project.slides[sn-1].get_img()[y:y+h, x:x+w]

            project.slides[sn-1].add_target(x, y, data)
    print("COMPLETE")
    
    return project

def load_stalign_runner():
    project = load_target_processor()
    # TODO: implement
    return project

def load_segmentation_importer():
    project = load_slide_processor()
    # TODO: implement
    return project

def load_visualign_runner():
    project = load_segmentation_importer()
    # TODO: implement
    return project

def load_region_picker():
    project = load_starter()
    # TODO: implement
    return project

def load_exporter():
    project = load_starter()
    # TODO: implement
    return project
