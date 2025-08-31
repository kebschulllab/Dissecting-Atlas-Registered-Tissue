import json
import pytest
import shutil
import os

from ..pages import Starter
from .load import load_starter
from .utils import EXAMPLE_FOLDER

@pytest.fixture
def project():
    return load_starter()

@pytest.fixture
def starter(master, project):
    return Starter(master, project)

@pytest.fixture
def activated_starter(starter):
    starter.activate()
    return starter

@pytest.fixture
def slides_dir():
    return os.path.join(
        os.path.dirname(__file__), 
        '..', 
        '..',
        'demo_images'
    )

@pytest.fixture(params=list(range(2)))
def seg_method(activated_starter, request):
    values = activated_starter.segmentation_method_combobox['values']
    return values[request.param]

@pytest.fixture()
def atlas_name(activated_starter):
    path = os.path.join(
        os.path.dirname(__file__),
        EXAMPLE_FOLDER,
        'atlas.json'
    )
    with open(path, 'r') as f:
        data = json.load(f)
        return data

@pytest.fixture
def completed_starter(activated_starter, slides_dir, seg_method, atlas_name):
    starter = activated_starter
    starter.slides_folder_name.set(slides_dir)
    starter.atlas_name.set(atlas_name)
    starter.segmentation_method.set(seg_method)
    
    yield starter

    # Cleanup after test
    for folder in os.listdir(slides_dir):
        if folder.startswith("DART"):
            full_path = os.path.join(slides_dir, folder)
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)

def test_done(completed_starter, seg_method, atlas_name):
    starter = completed_starter

    starter.stalign_skipped = False
    def skip_stalign():
        starter.stalign_skipped = True
    starter.winfo_toplevel().skip_inbuilt_segmentation = skip_stalign

    starter.done()

    if "Other" in seg_method:
        assert starter.stalign_skipped
    else:
        assert not starter.stalign_skipped
    assert starter.project.folder is not None
    assert os.path.isdir(starter.project.folder)

    atlas_path = os.path.join(
        starter.project.folder,
        'atlas.json'
    )
    assert os.path.exists(atlas_path)
    with open(atlas_path, 'r') as f:
        atlas = json.load(f)
        assert atlas_name == atlas
