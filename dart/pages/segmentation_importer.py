import os
import shutil
import skimage as ski
import tkinter as tk
from tkinter import ttk

from pages.base import BasePage
from utils import TkFigure, get_filename, get_folder

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
        self.upload_path = None
    
    def create_widgets(self):
        """
        Create the widgets for this page. This includes:
        - Instructions label: A label with instructions for the user to follow
        - Load Button: A button that will call self.load when clicked
        - Results Frame: Contains figure displaying results along with
        navigation controls
        """
        self.instructions_label = ttk.Label(
            master=self,
            text="Instructions: \n"
                 "1. Generate segmentations of the target images in the "
                 "project folder using your desired algorithm. \n"
                 "2. Upload segmentations to the folder titled "
                 "\"UPLOAD_SEGMENTATION_HERE\" which can be found inside the "
                 "project folder. \n\n" 
                 "Segmentation Requirements: \n"
                 "1. Uses the Allen Atlas CCF's pixel value to brain region "
                 "assignments \n"
                 "2. The segmentation(s) are .tif files, and the filename is "
                 "that of the corresponding image with \"_seg\" appended to it \n"
                 "For example: \"slide1_target1_seg.tif\""
        )

        self.load_btn = ttk.Button(
            master=self,
            text="Load Segmentation(s)",
            command=self.load
        )

        self.results_viewer = tk.Frame(self)
        self.create_result_viewer()
    
    def show_widgets(self):
        """
        Show the widgets for this page. This method simply packs the 
        instructions label
        """
        self.instructions_label.pack()
        self.load_btn.pack()
    
    def load(self):
        """
        Load the segmentations. This method searches for the segmentations in 
        the project folder using the naming guide. It then reads them in as
        numpy arrays and adds them to the corresponding targets segmentation
        dictionary under the key "custom". Then, it notifies the user of 
        successful upload via terminal or it raises an exception if a 
        segmentation is missing. After saving the segmentation results in the
        corresponding folder, it hides the load button and calls
        `show_results` to display the uploaded segmentations.
        """
        # TODO: implement me

        for si, slide in enumerate(self.slides):
            for ti, target in enumerate(slide.targets):

                # read segmentation
                filename = get_filename(si, ti) + '_seg.tif'
                path = os.path.join(
                    self.upload_path,
                    filename
                )
                try:
                    seg = ski.io.imread(path, plugin='pil')
                except:
                    raise Exception(
                        f"Missing segmentation for Slide #{si+1}, "
                        f"Target #{ti+1}"
                    )
                target.seg['custom'] = seg
                print(
                    f"Segmentation of Slide #{si+1}, Target #{ti+1} "
                    "successfully uploaded."
                )
        
                # make target folder and save segmentation
                folder = os.path.join(
                    self.project.folder, 
                    get_folder(si, ti, 0)
                )
                os.makedirs(folder, exist_ok=True)
                target.save_seg(folder, 'custom')

        self.instructions_label.pack_forget()
        self.load_btn.pack_forget()
        self.show_results()

    def create_result_viewer(self):
        """
        Create the widgets in the results frame. These include:
        - Menu Frame: Contains navigation controls for viewing results
        of each target.
        - Slice Frame: Contains the figure to display the target image
        with the boundaries from the segmentation overlaid.
        """
        
        # for showing results after running stalign
        self.menu_frame = tk.Frame(self.results_viewer)
        self.slice_frame = tk.Frame(self.results_viewer)

        self.slide_nav_label = ttk.Label(self.menu_frame, text="Slide: ")
        self.curr_slide_var = tk.IntVar(master=self.menu_frame, value='1')
        self.slide_nav_combo = ttk.Combobox(
            master=self.menu_frame,
            values=[],
            state='readonly',
            textvariable=self.curr_slide_var,
        )
        self.slide_nav_combo.bind('<<ComboboxSelected>>', self.switch_slides)

        self.target_nav_label = ttk.Label(self.menu_frame, text="Target: ")
        self.curr_target_var = tk.IntVar(master=self.menu_frame, value='1')
        self.target_nav_combo = ttk.Combobox(
            master=self.menu_frame,
            values=[],
            state='readonly',
            textvariable=self.curr_target_var,
        )
        self.target_nav_combo.bind('<<ComboboxSelected>>', self.update_result_viewer)

        self.slice_viewer = TkFigure(self.slice_frame, toolbar=True)

    def show_result_viewer(self):
        """
        Show the results viewer. This method displays the widgets 
        inside the results frame with pack and grid configuration.
        """
        
        self.results_viewer.grid_rowconfigure(1, weight=1)
        self.results_viewer.grid_columnconfigure(0, weight=1)
        self.menu_frame.grid(row=0, column=0, sticky='nsew')
        self.slice_frame.grid(row=1, column=0, sticky='nsew')

        self.slide_nav_label.pack(side=tk.LEFT)
        self.slide_nav_combo.pack(side=tk.LEFT)
        
        self.target_nav_combo.pack(side=tk.RIGHT)
        self.target_nav_label.pack(side=tk.RIGHT)

        self.slice_viewer.get_widget().pack(expand=True, fill=tk.BOTH)
    
    def update_result_viewer(self, event=None):
        """
        Update the figure displaying the result. This method gets the
        current slide and target indices, ensures the dropdowns are 
        correctly configured, and displays the results for the current
        target.

        Parameters
        ----------
        event : tk.Event, optional
            The event that triggered the update (default is None).
        """
        
        self.currSlide = self.slides[self.get_slide_index()]
        self.currTarget = self.currSlide.targets[self.get_target_index()]
        self.target_nav_combo.config(
            values=[i+1 for i in range(self.currSlide.numTargets)]
        )
        self.show_seg()

    def show_seg(self):
        """
        Show the current target with the region boundaries overlaid.
        This method clears the results display then shows the results
        for the current target.
        """
        
        self.slice_viewer.axes[0].cla()

        if 'stalign' in self.currTarget.seg:
            seg_img = self.currTarget.get_img(seg='stalign')
        else:            
            seg_img = self.currTarget.get_img()
        
        self.slice_viewer.axes[0].imshow(seg_img)
        self.slice_viewer.update()

    def show_results(self):
        """
        Show the results frame. This method updates the figure to display
        the current target's results, ensures the navigation controls are 
        correctly configured, and packs the results frame so that it's 
        visible.
        """

        self.results_viewer.pack(expand=True, fill=tk.BOTH)
        self.show_result_viewer()

        self.currSlide = None
        self.currTarget = None
        self.update_result_viewer()
        self.slide_nav_combo.config(
            values=[i+1 for i in range(len(self.slides))]
        )

    def switch_slides(self, event=None):
        """
        Switch to the selected slide in the slide navigation combobox. This method
        retrieves the selected slide index from the combobox, updates the current
        slide, and updates the target navigation combobox to reflect the targets
        available for the selected slide. It also resets the new points and updates
        the target and atlas images in the slice viewer.
        
        Parameters
        ----------
        event : tk.Event, optional
            The event that triggered the switch (default is None).
        """
        self.curr_target_var.set(1)
        self.update_result_viewer()
    
    def get_slide_index(self):
        """
        Get the index of the current slide based on the selected value in the
        slide navigation combobox. The index is adjusted to be zero-based by
        subtracting 1 from the selected value.
        
        Returns
        -------
        index : int
            The index of the current slide.
        """
        return self.curr_slide_var.get()-1
    
    def get_target_index(self):
        """
        Get the index of the current target based on the selected value in the
        target navigation combobox. The index is adjusted to be zero-based by 
        subtracting 1 from the selected value.
        
        Returns
        -------
        index : int
            The index of the current target.
        """

        return self.curr_target_var.get()-1

    def activate(self):
        """
        Activate this page. This method calls the parent class's activate
        method and creates a folder within the project folder where the 
        user can upload their segmentations.
        """

        self.upload_path = os.path.join(
            self.project.folder,
            'UPLOAD_SEGMENTATION_HERE'
        )
        os.makedirs(self.upload_path)
        super().activate()
    
    def deactivate(self):
        """
        Deactivate this page. This method calls the parent class's deactivate 
        method and deletes the folder for uploading segmentations.
        """

        self.results_viewer.pack_forget()
        shutil.rmtree(self.upload_path)
        self.upload_path = None
        super().deactivate()
    
    def done(self):
        """
        Finalize the SegmentationImporter's actions. This method confirms that
        a segmentation has been imported for each target. If not, it raises an
        Exception and informs the user which targets are lacking segmentations.
        """
        # TODO: implement me!
        for si, slide in enumerate(self.slides):
            for ti, target in enumerate(slide.targets):
                if "custom" not in target.seg:
                    raise Exception(
                        f"Missing segmentation for Slide #{si+1}, "
                        f"Target #{ti+1}"
                    )

        super().done()
    
    def cancel(self):
        """
        Cancel the SegmentationImporter's actions. This method clears the 
        custom segmentation for each target, if it exists, and also hides the
        resuls frame.
        """

        for slide in self.slides:
            for target in slide.targets:
                if 'custom' in target.seg:
                    target.seg.pop('custom')
        super().cancel()