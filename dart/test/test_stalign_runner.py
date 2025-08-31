import filecmp
import pytest
import shutil
import os

from dart.pages import STalignRunner
from dart.utils import get_target_name
from dart.test.load import load_stalign_runner
from dart.test.utils import EXAMPLE_FOLDER

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



