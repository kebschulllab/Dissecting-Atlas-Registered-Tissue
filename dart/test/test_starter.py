import json
import pandas as pd
import pytest
import shutil
import tkinter as tk

from ..pages import Starter
from .load import load_starter
import os


@pytest.fixture
def project():
    return load_starter()

@pytest.fixture
def master():
    root = tk.Tk()
    yield root
    root.destroy()

@pytest.fixture
def starter(master, project):
    return Starter(master, project)

@pytest.fixture
def activated_starter(starter):
    starter.activate()
    return starter

@pytest.fixture
def completed_starter(activated_starter, monkeypatch, slides_dir):
    starter = activated_starter
    starter.slides_folder_name.set(slides_dir)
    # Tests will supply combinations of atlas and segmentation method
    
    yield starter

    # Cleanup after test
    for folder in os.listdir(slides_dir):
        if folder.startswith("DART"):
            full_path = os.path.join(slides_dir, folder)
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)

@pytest.fixture
def slides_dir():
    return os.path.join(
        os.path.dirname(__file__), 
        '..', 
        '..',
        'demo_images'
    )

@pytest.fixture
def seg_method(completed_starter):
    return completed_starter.segmentation_method_combobox['values']

@pytest.fixture
def atlas_name(completed_starter):
    return completed_starter.atlas_picker_combobox['values']


def test_init(starter):
    assert hasattr(starter, "segmentation_method")
    assert hasattr(starter, "atlas_name")
    assert hasattr(starter, "slides_folder_name")

def test_activate(activated_starter):
    starter = activated_starter
    
    # Check if atlas picker is populated
    assert len(starter.atlas_picker_combobox['values']) > 0
    print(starter.atlas_picker_combobox['values'])
    # Check if all widgets are gridded
    assert all([slave.winfo_manager == 'grid' for slave in starter.slaves()])

def test_select_slides(activated_starter, slides_dir, monkeypatch):
    starter = activated_starter
    monkeypatch.setattr(tk.filedialog, "askdirectory", lambda **kwargs: slides_dir)
    starter.select_slides()
    assert starter.slides_folder_name.get() == slides_dir

@pytest.mark.parametrize("seg_method", [], indirect=True)
@pytest.mark.parametrize("atlas_name", [], indirect=True)
def test_done_success(completed_starter, seg_method, atlas_name):
    starter = completed_starter
    starter.atlas_name.set(atlas_name)
    starter.segmentation_method.set(seg_method)
    starter.done()

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

'''
@pytest.mark.parametrize("seg_method,atlas,slides,err", [
    ("Choose Segmentation Method", "TestAtlas", "folder", "Must select a segmentation method."),
    ("DART in-built (STalign + VisuAlign)", "Choose Atlas", "folder", "Must select an atlas."),
    ("DART in-built (STalign + VisuAlign)", "TestAtlas", "", "Must select an folder containing sample images."),
])
def test_done_missing_fields(master, project, seg_method, atlas, slides, err):
    starter = Starter(master, project)
    starter.create_widgets()
    starter.segmentation_method.set(seg_method)
    starter.atlas_name.set(atlas)
    starter.slides_folder_name.set(slides)
    with pytest.raises(Exception) as excinfo:
        starter.done()
    assert err in str(excinfo.value)

def test_load_atlas_info(monkeypatch, master, project, atlas_dir):
    starter = Starter(master, project)
    starter.atlas_dir = str(atlas_dir)
    starter.atlases = {k: DummyAtlas() for k in ["FSR", "FSL", "DSR", "DSL"]}
    monkeypatch.setattr(pd, "read_csv", lambda *a, **kw: pd.DataFrame({"id": [0]}, index=["empty"]))
    starter.load_atlas_info("TestAtlas")
    assert "names" in starter.atlases

def test_load_slides(master, project, slides_dir, monkeypatch):
    class DummySlide:
        def __init__(self, path): self.path = path
    monkeypatch.setattr("pages.starter.Slide", DummySlide)
    starter = Starter(master, project)
    starter.slides = []
    starter.load_slides(str(slides_dir))
    assert len(starter.slides) == 2

def test_cancel(master, project):
    starter = Starter(master, project)
    # Should call super().cancel() without error
    starter.cancel()'''
