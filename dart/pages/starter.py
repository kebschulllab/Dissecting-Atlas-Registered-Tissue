from datetime import datetime
import json
import tkinter as tk
from tkinter import ttk
import os
import pandas as pd

from pages.base import BasePage
from images import Slide
from constants import FSR, DSR, FSL, DSL

class Starter(BasePage):
    """
    Page for selecting the atlas and slides to process.
    This page allows the user to choose an atlas and a folder containing
    sample images. It initializes the atlas and slide information, and
    sets up the project structure.
    """

    def __init__(self, master, project):
        super().__init__(master, project)
        self.header = 'Select samples and atlas'
        self.atlas_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            '..',
            '..',
            'atlases'
        )

    def activate(self):
        """
        Activate the Starter page. This method is called when the page is
        displayed. It configures the atlas combobox and shows the widgets.
        """

        atlases = os.listdir(self.atlas_dir)
        self.atlas_picker_combobox.config(values=atlases)
        super().activate()

    
    def create_widgets(self):
        """
        Create widgets for the Starter page. This includes:
        - Atlas picker: A combobox to select an atlas from available atlases.
        - Slides picker: An entry field to select a folder containing sample images.
        - Browse button: A button to open a file dialog for selecting the slides folder.
        """
        # Segmentation Method Picker
        self.segmentation_method = tk.StringVar(
            master=self, 
            value="DART in-built (STalign + VisuAlign)"
        )
        self.segmentation_method_label = ttk.Label(
            self, 
            text="Segmentation Method:"
        )
        self.segmentation_method_combobox = ttk.Combobox(
            master=self, 
            values=['DART in-built (STalign + VisuAlign)', 
                    'Other - I will provide the segmentation results'],
            state='readonly',
            textvariable=self.segmentation_method
        )

        # Atlas Picker
        self.atlas_name = tk.StringVar(master=self, value="Choose Atlas")
        self.atlas_picker_label = ttk.Label(self, text="Atlas:")
        self.atlas_picker_combobox = ttk.Combobox(
            master=self,
            state='readonly',
            textvariable=self.atlas_name
        )

        # Slides Picker
        self.slides_folder_name = tk.StringVar(master=self)
        self.slides_picker_label = ttk.Label(self, text="Samples:")
        self.slides_picker_entry = ttk.Entry(
            master=self,
            textvariable=self.slides_folder_name
        )
        self.browse_button = ttk.Button(
            master=self,
            text="Browse",
            command=self.select_slides
        )

    def show_widgets(self):
        """
        Show the widgets for the Starter page. This method arranges the widgets
        in a grid layout and configures their appearance.
        """

        # configure columns
        self.grid_columnconfigure(0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2)

        # show widgets using grid()
        self.segmentation_method_label.grid(row=0, column=0)
        self.segmentation_method_combobox.grid(row=0, column=1, sticky='ew')
        self.atlas_picker_label.grid(row=1, column=0)
        self.atlas_picker_combobox.grid(row=1, column=1, sticky='ew')
        self.slides_picker_label.grid(row=2, column=0)
        self.slides_picker_entry.grid(row=2, column=1, sticky='ew')
        self.browse_button.grid(row=2, column=2)
    
    def select_slides(self):
        """
        Open a file dialog to select a folder containing sample images.
        """
        folder_name = tk.filedialog.askdirectory(
            parent=self, 
            initialdir=os.curdir,
            mustexist=True
        )
        self.slides_folder_name.set(folder_name)
    
    def done(self):
        """
        Finalize the Starter page's actions. This method checks that the user
        has selected an atlas and a folder containing sample images. It then
        loads the atlas information and the slides into the project structure.
        Raises an exception if the atlas or slides folder is not selected.
        """
        # check that segmentation method picker, atlas picker, 
        # and slides picker are not blank
        if  self.segmentation_method.get() == 'Choose Segmentation Method':
            raise Exception('Must select a segmentation method.')
        elif self.atlas_name.get() == 'Choose Atlas': 
            raise Exception('Must select an atlas.')
        elif self.slides_folder_name.get() == '':
            raise Exception('Must select an folder containing sample images.')

        seg_method = self.segmentation_method.get()
        if seg_method == 'Other - I will provide the segmentation results':
            self.winfo_toplevel().skip_inbuilt_segmentation()
            print("Skipping in-built segmentation steps.")

        # load atlases
        self.load_atlas_info(self.atlas_name.get())

        # load slides
        path = self.slides_folder_name.get()
        if not os.path.exists(path): 
            raise Exception(
                'Could not find slides folder at the specified path: ' + path
            )
        self.load_slides(path)

        # create project folder
        folder = "DART-" + datetime.now().strftime("%Y-%m-%d_%H%M%S")
        os.mkdir(os.path.join(path, folder))
        self.project.parent_folder = os.path.abspath(path)
        self.project.folder = os.path.join(
            self.project.parent_folder, 
            folder
        )
        
        # save atlas name
        with open(os.path.join(self.project.folder, 'atlas.json'), 'w') as f:
            json.dump(self.rois, f)

        super().done()

    def load_atlas_info(self, name):
        """
        Load atlas information from the specified path. This method searches for
        the atlas files in the given directory and initializes the atlases
        with the reference and label images. It also loads the names dictionary
        for the atlas.
        
        Parameters
        ----------
        name : str
            The name of the atlas to be loaded.
        """
        path = os.path.join(self.atlas_dir, name)
        for filename in os.listdir(path):
            curr_path = os.path.join(path, filename)
            if 'reference' in filename: 
                ref_atlas_filename = curr_path
            elif 'label' in filename:
                lab_atlas_filename = curr_path
            elif 'names_dict' in filename:
                names_dict_filename = curr_path

        self.atlases[FSR].load_img(path=ref_atlas_filename)
        self.atlases[FSL].load_img(path=lab_atlas_filename, normalize=False)

        # load images for downscaled version, 
        # which should be at least 50 microns per pixel
        pix_dim_full = self.atlases[FSR].pix_dim
        downscale_factor = tuple([int(max(1, 50/dim)) for dim in pix_dim_full])
        self.atlases[DSR].load_img(
            img=self.atlases[FSR].img, 
            pix_dim=self.atlases[FSR].pix_dim, 
            ds_factor=downscale_factor
        )
        self.atlases[DSL].load_img(
            img=self.atlases[FSL].img, 
            pix_dim=self.atlases[FSL].pix_dim, 
            ds_factor=downscale_factor,
            normalize=False
        )
        self.atlases['names'] = pd.read_csv(
            names_dict_filename, 
            index_col='name'
        )
        self.atlases['names'].loc['empty','id'] = 0

    def load_slides(self, path):
        """
        Load slides from the specified path. This method searches for image files
        in the given directory and initializes Slide objects for each image file.
        It also creates a new folder for the project based on the current date and
        time.
        
        Parameters
        ----------
        path : str
            The path to the directory containing the sample images.
        """
        for f in os.listdir(path):
            curr_path = os.path.join(path, f)
            isImage = curr_path.lower().endswith(
                ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif')
            )
            if os.path.isfile(curr_path) and isImage:
                new_slide = Slide(curr_path)
                self.slides.append(new_slide)
        
        # TODO: raise exception if no slides found

    def cancel(self):
        """
        Cancel the actions on the Starter page.
        """
        super().cancel()