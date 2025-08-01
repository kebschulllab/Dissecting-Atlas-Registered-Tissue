import os

from pages.base import BasePage

class SegmentationImporter(BasePage):
    """
    Page for importing user's custom segmentation. This page instructs the 
    user to apply their custom segmentation algorithm on the target images 
    created in the previous step. Once the user has created the segmentations
    and uploaded them to the project folder in the correct locations with the
    correct names, this class reads the segmentations and displays the targets
    with their boundaries overlaid. 
    """

    def __init__(self, master, project):
        super().__init__(master, project)
        self.header = "Perform custom segmentation and import results here"
    
    def create_widgets(self):
        return super().create_widgets()
    
    def show_widgets(self):
        return super().show_widgets()
    
    def activate(self):
        return super().activate()
    
    def deactivate(self):
        return super().deactivate()
    
    def done(self):
        return super().done()
    
    def cancel(self):
        return super().cancel()