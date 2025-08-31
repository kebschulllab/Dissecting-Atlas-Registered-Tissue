import filecmp
import pytest
import shutil
import os

from ..pages import VisuAlignRunner
from ..utils import get_target_name
from .load import load_visualign_runner
from .utils import EXAMPLE_FOLDER

@pytest.fixture(scope="module")
def project():
	loaded_project = load_visualign_runner()
	yield loaded_project
	shutil.rmtree(loaded_project.folder)

@pytest.fixture
def visualign_runner(master, project):
	return VisuAlignRunner(master, project)

@pytest.fixture
def activated_visualign_runner(visualign_runner):
	visualign_runner.activate()
	return visualign_runner

@pytest.fixture
def completed_visualign_runner(activated_visualign_runner):
    vr = activated_visualign_runner

    # copy visualign results into project folder
    src_dir = os.path.join(
        os.path.dirname(__file__),
		EXAMPLE_FOLDER,
		"EXPORT_VISUALIGN_HERE"
    )
    dest_dir = os.path.join(
		vr.project.folder,
		"EXPORT_VISUALIGN_HERE"
    )
    shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
	
    vr.load_results()
    return vr


def test_done(completed_visualign_runner):
	vr = completed_visualign_runner
	vr.done()
	
    # check that each target has a visualign segmentation
	for slide in vr.slides:
		for target in slide.targets:
			assert 'visualign' in target.seg
    
    # check that results were saved correctly
	for sn,slide in enumerate(vr.slides):
		for tn,target in enumerate(slide.targets):
			act_folder_path = os.path.join(
				vr.project.folder,
				get_target_name(sn,tn)
            )
			exp_folder_path = os.path.join(
				os.path.dirname(__file__),
				EXAMPLE_FOLDER,
				get_target_name(sn,tn)
            )
			
            # check all visualign output files
			check_name = lambda name: 'visualign' in name
			files_to_check = [
				name 
				for name in os.listdir(act_folder_path)
				if check_name(name)
            ]
			
			for filename in files_to_check:
				act_path = os.path.join(act_folder_path, filename)
				exp_path = os.path.join(exp_folder_path, filename)
				assert filecmp.cmp(act_path, exp_path, shallow=False)

