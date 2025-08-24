from app import Project

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
    project = load_starter()
    # TODO: implement
    return project

def load_target_processor():
    project = load_slide_processor()
    # TODO: implement
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
