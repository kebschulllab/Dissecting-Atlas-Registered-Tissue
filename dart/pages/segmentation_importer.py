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
        """
        Create the widgets for this page. This includes:
        - Instructions label: A label with instructions for the user to follow
        """
    
    def show_widgets(self):
        """
        Show the widgets for this page. This method simply packs the 
        instructions label
        """
    
    def activate(self):
        """
        Activate this page. This method calls the parent class's activate
        method.
        """
        super().activate()
    
    def deactivate(self):
        """
        Deactivate this page. This method calls the parent class's deactivate 
        method.
        """
        super().deactivate()
    
    def done(self):
        """
        Finalize the SegmentationImporter's actions. This method confirms that
        a segmentation has been imported for each target. If not, it raises an
        Exception and informs the user which targets are lacking segmentations.
        The method also loads the segmentations in Target.seg['custom']
        """
        super().done()
    
    def cancel(self):
        """
        Cancel the SegmentationImporter's actions. This method clears the 
        custom segmentation for each target, if it exists.
        """
        super().cancel()