import filecmp
import itertools
import numpy as np
import pytest
import shutil
import os

from dart.pages import Exporter
from dart.utils import get_target_name
from dart.test.load import load_exporter
from dart.test.utils import EXAMPLE_FOLDER, DummyEvent

@pytest.fixture(scope="module")
def project():
	loaded_project = load_exporter()
	yield loaded_project
	shutil.rmtree(loaded_project.folder)

@pytest.fixture
def exporter(master, project):
	return Exporter(master, project)

@pytest.fixture
def activated_exporter(exporter):
	exporter.activate()
	return exporter

@pytest.fixture
def completed_exporter(activated_exporter):
    ex = activated_exporter
	
    # export every combination of targets
    for sn,slide in enumerate(ex.slides):
        ex.curr_slide_var.set(sn+1)
        ex.update()
        for export_combo in get_all_combs(slide):
            simulate_export(ex, export_combo)
	
    return ex

def get_all_combs(slide):
    combs = []
    numTargets = slide.numTargets
    for count in range(1, numTargets+1):
        combs.append(itertools.combinations(slide.targets, count))
    return itertools.chain.from_iterable(combs)

def simulate_export(ex, targets):
    for target in targets:
        # click target
        x = target.x_offset
        y = target.y_offset
        axes = ex.slide_viewer.axes[0]
        event = DummyEvent(x, y, axes, 1)
        ex.on_click(event)

    # click export
    ex.export()

def test_done(completed_exporter):
    ex = completed_exporter
	
    for si,slide in enumerate(ex.slides):
        for ti,target in enumerate(slide.targets):
            
            # check that each targets outlines .xml file has been saved
            act_path = os.path.join(
				ex.project.folder,
				get_target_name(si,ti),
				'outlines_ldm.xml'
            )
            exp_path = os.path.join(
				os.path.dirname(__file__),
				EXAMPLE_FOLDER,
				get_target_name(si,ti),
				'outlines_ldm.xml'
            )
            assert filecmp.cmp(act_path, exp_path, shallow=False)
			
            # check that each target's roi outlines image has been saved
            act_path = os.path.join(
				ex.project.folder,
				get_target_name(si,ti),
				'rois.png'
            )
            exp_path = os.path.join(
                os.path.dirname(__file__),
				EXAMPLE_FOLDER,
				get_target_name(si,ti),
				'rois.png'
            )
            assert filecmp.cmp(act_path, exp_path, shallow=False)
			
	# check that outputs folder is identical
    act_folder = os.path.join(
		ex.project.folder,
		"output"
    )
    exp_folder = os.path.join(
		os.path.dirname(__file__),
		EXAMPLE_FOLDER,
		"output"
    )
    cmp = filecmp.dircmp(act_folder, exp_folder)
    print(cmp.diff_files)
    assert len(cmp.diff_files)==0
