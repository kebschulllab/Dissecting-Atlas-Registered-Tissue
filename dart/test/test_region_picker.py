import filecmp
import json
import pytest
import shutil
import os

from dart.pages import RegionPicker
from dart.utils import get_target_name
from dart.test.load import load_region_picker
from dart.test.utils import EXAMPLE_FOLDER

@pytest.fixture(scope="module")
def project():
	loaded_project = load_region_picker()
	yield loaded_project
	shutil.rmtree(loaded_project.folder)

@pytest.fixture
def region_picker(master, project):
	return RegionPicker(master, project)

@pytest.fixture
def activated_region_picker(region_picker):
	region_picker.activate()
	return region_picker

@pytest.fixture
def completed_region_picker(activated_region_picker):
    rp = activated_region_picker
	
    # get regions list
    path = os.path.join(
		os.path.dirname(__file__),
		EXAMPLE_FOLDER,
		"regions.json"
    )
    with open(path, 'r') as f:
        rois = json.load(f)
    
    # click on rois by checking ancestors and descendants
    for roi in rois:
        roi = float(roi)
        rp.region_tree._check_ancestor(roi)
        rp.region_tree._check_descendant(roi)
    rp.update()
	
    return rp

def test_done(completed_region_picker):
	rp = completed_region_picker
	rp.done()
	
    # check that each target has region boundaries and wells with same keys
	for slide in rp.slides:
		for target in slide.targets:
			bounds = target.region_boundaries
			wells = target.wells
			assert bounds.keys() == wells.keys()

    # check that regions list saved correctly
	act_path = os.path.join(
		rp.project.folder,
		"regions.json"
    )
	exp_path = os.path.join(
		os.path.dirname(__file__),
		EXAMPLE_FOLDER,
		"regions.json"
    )
	assert filecmp.cmp(act_path, exp_path, shallow=False)

