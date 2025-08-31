import filecmp
import imageio as iio
import numpy.testing as npt
import pytest
import shutil
import os

from ..pages import SegmentationImporter
from ..utils import get_target_name
from .load import load_segmentation_importer
from .utils import EXAMPLE_FOLDER

@pytest.fixture(scope="module")
def project():
	loaded_project = load_segmentation_importer()
	yield loaded_project
	shutil.rmtree(loaded_project.folder)

@pytest.fixture
def segmentation_importer(master, project):
	return SegmentationImporter(master, project)

@pytest.fixture
def activated_segmentation_importer(segmentation_importer):
	segmentation_importer.activate()
	return segmentation_importer

@pytest.fixture
def completed_segmentation_importer(activated_segmentation_importer):
    seg_imp = activated_segmentation_importer
	
    # copy segmentations to UPLOAD_SEGMENTATION_HERE folder
    for sn,slide in enumerate(seg_imp.slides):
        for tn,target in enumerate(slide.targets):
            folder_path = os.path.join(
                os.path.dirname(__file__),
                EXAMPLE_FOLDER,
                get_target_name(sn,tn)
            )

            path = os.path.join(folder_path, "stalign_segmentation.tif")
            if not os.path.exists(path):
                path = os.path.join(folder_path, "estimated_segmentation.tif")
            
            seg = iio.imread(path)

            name = get_target_name(sn,tn) + "_seg.tif"
            save_path = os.path.join(
                seg_imp.project.folder,
                "UPLOAD_SEGMENTATION_HERE",
                name
            )
            iio.imsave(save_path, seg)

    # load segmentations
    seg_imp.load()

    return seg_imp

def test_done(completed_segmentation_importer):
    seg_imp = completed_segmentation_importer
    seg_imp.done()

    for sn,slide in enumerate(seg_imp.slides):
        for tn,target in enumerate(slide.targets):
            assert 'custom' in target.seg

            act_folder_path = os.path.join(
                seg_imp.project.folder,
                get_target_name(sn,tn)
            )
            exp_folder_path = os.path.join(
                os.path.dirname(__file__),
                EXAMPLE_FOLDER,
                get_target_name(sn,tn)
            )

            exp_seg = 'stalign'
            
            # compare .tif segmentation
            act_path = os.path.join(
                act_folder_path,
                "custom_segmentation.tif"
            )
            exp_path = os.path.join(
                exp_folder_path,
                exp_seg + "_segmentation.tif"
            )
            if not os.path.exists(exp_path):
                exp_seg = "estimated"
                exp_path = os.path.join(
                    exp_folder_path,
                    exp_seg + "_segmentation.tif"
                )
            seg_act = iio.imread(act_path)
            seg_exp = iio.imread(exp_path)
            npt.assert_array_equal(seg_act, seg_exp)

            # compare .tif outlines image
            act_path = os.path.join(
                act_folder_path,
                "custom_outlines.tif"
            )
            exp_path = os.path.join(
                exp_folder_path,
                exp_seg + "_outlines.tif"
            )
            img_act = iio.imread(act_path)
            img_exp = iio.imread(exp_path)
            npt.assert_array_equal(img_act, img_exp)
            
            # compare .png outlines image
            act_path = os.path.join(
                act_folder_path,
                "custom_outlines.png"
            )
            exp_path = os.path.join(
                exp_folder_path,
                exp_seg + "_outlines.png"
            )
            img_act = iio.imread(act_path)
            img_exp = iio.imread(exp_path)
            npt.assert_array_equal(img_act, img_exp)

            

