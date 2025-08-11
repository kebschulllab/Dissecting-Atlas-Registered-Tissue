import os
import tkinter as tk
from tkinter import ttk

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
        self.instructions_label = ttk.Label(
            master=self,
            text=""
        )

        self.load_btn = ttk.Button(
            master=self,
            text="Load Segmentation(s)",
            command=self.load
        )
    
    def show_widgets(self):
        """
        Show the widgets for this page. This method simply packs the 
        instructions label
        """
        self.instructions_label.pack()
        # instructions:
        # take the target images we generated from the project folder
        # and segment them with whatever algorithm you want
        # as of now, the only requirement for the segmentation is that
        # it uses the allen atlas's pixel value to brain region assignments
        # for more info see: ___ (some link)
        # then, once you have this segmentation, copy the file over as a .tif
        # with the name of the corresponding image (e.g. "slide1_target1") with "_seg" 
        # appended
    
    def load():
        """
        Load the segmentations. This method searches for the segmentations in 
        the project folder using the naming guide. It then reads them in as
        numpy arrays and adds them to the corresponding targets segmentation
        dictionart under the key "custom". Then, it notifies the user of 
        successful upload via terminal or it raises an exception if a 
        segmentation is missing. Finally, it hides the load button and calls
        `show_results` to display the uploaded segmentations.
        """
        # TODO: implement me
        return

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