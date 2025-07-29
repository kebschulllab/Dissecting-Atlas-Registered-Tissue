from datetime import datetime
import glob
import json
import matplotlib as mpl
import numpy as np
import os
import pandas as pd
import pickle
import PIL.Image
import PIL.ImageDraw
import shapely
import shutil
from sklearn.cluster import dbscan
import tkinter as tk
from tkinter import ttk
import ttkwidgets
import torch

from images import *
from constants import *
from utils import *

from abc import ABC, abstractmethod

class Page(tk.Frame, ABC):
    """
    Abstract base class for all pages in the application.
    Each page should inherit from this class and implement the abstract methods.
    
    
    Attributes
    ----------
        master : tk.Frame
            The parent window.
        project : dict 
            The project data containing slides and atlases.
        slides : list
            List of Slide objects.
        atlases : dict 
            Dictionary containing atlas information.
        header : str
            Header text for the page.
        
    Parameters
    ----------
        master : tk.Frame 
            The parent window.
        project : dict
            The project data containing slides and atlases.
    """

    def __init__(self, master, project):
        super().__init__(master)
        self.project = project
        self.slides = self.project.slides
        self.atlases = self.project.atlases
        self.header = ""
        self.create_widgets()

    @abstractmethod
    def create_widgets(self): 
        """
        Abstract method to create widgets for the page. Each subclass should
        implement this method to create its own widgets. This method is
        responsible for initializing and setting up all widgets that will be
        used on the page. Widgets should be configured here, but not packed or
        gridded; layout should be handled in show_widgets().
        """
        pass

    @abstractmethod
    def show_widgets(self): 
        """
        Abstract method to show the widgets on the page. Each subclass should
        implement this method to arrange and display its widgets. This method is
        responsible for laying out and displaying all widgets that belong to the
        page, using the preferred geometry manager.
        """
        pass

    def activate(self):
        """
        Activate the page by packing it into the parent frame and displaying its
        widgets. This method should be called when the page is to be displayed.
        Subclasses may add extra functionality to this method as needed.
        """
        self.pack(expand=True, fill=tk.BOTH)
        self.show_widgets()
    
    def deactivate(self):
        """
        Deactivate the page by hiding it. This method should be called when the
        page is no longer needed. It will remove the page from the view, but not
        destroy it. Subclasses may override this method to add additional
        cleanup functionality.
        """
        self.pack_forget()
    
    @abstractmethod
    def done(self):
        """
        Abstract method to finalize the page's actions. This method is called
        when the user presses the "Next" button. The user has completed their
        actions on the page and is ready to proceed. It should handle any
        necessary validation or data processing before moving to the next page.
        This method should also deactivate the page.
        """
        self.deactivate()

    @abstractmethod
    def cancel(self):
        """
        Abstract method to cancel the page's actions. This method is called when
        the user presses the "Previous" button. It should handle any necessary
        cleanup or state reset before returning to the previous page or exiting
        the application. This method should also deactivate the page.
        """
        self.deactivate()

    def get_header(self):
        """
        Returns the header text for the page.

        Returns
        -------
        self.header : str
            The header text for the page.
        """
        return self.header

class Starter(Page):
    """
    Page for selecting the atlas and slides to process.
    This page allows the user to choose an atlas and a folder containing
    sample images. It initializes the atlas and slide information, and
    sets up the project structure.
    """

    def __init__(self, master, project):
        super().__init__(master, project)
        self.header = 'Select samples and atlas'
    
    def create_widgets(self):
        """
        Create widgets for the Starter page. This includes:
        - Atlas picker: A combobox to select an atlas from available atlases.
        - Slides picker: An entry field to select a folder containing sample images.
        - Browse button: A button to open a file dialog for selecting the slides folder.
        """
        # Segmentation Method Picker
        self.segmentation_method = tk.StringVar(master=self, value="Choose Segmentation Method")
        self.segmentation_method_label = ttk.Label(self, text="Segmentation Method:")
        self.segmentation_method_combobox = ttk.Combobox(
            master=self, 
            values=['DART in-built (STalign + VisuAlign)', 
                    'Other - I will provide the segmentation results'],
            state='readonly',
            textvariable=self.segmentation_method
        )

        # Atlas Picker
        self.atlas_name = tk.StringVar(master=self, value="Choose Atlas")
        atlases = os.listdir(r'atlases')
        self.atlas_picker_label = ttk.Label(self, text="Atlas:")
        self.atlas_picker_combobox = ttk.Combobox(
            master=self, 
            values=atlases,
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
        atlas_folder_name = os.path.join('atlases', self.atlas_name.get())
        self.load_atlas_info(atlas_folder_name)

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

        super().done()

    def load_atlas_info(self, path):
        """
        Load atlas information from the specified path. This method searches for
        the atlas files in the given directory and initializes the atlases
        with the reference and label images. It also loads the names dictionary
        for the atlas.
        
        Parameters
        ----------
        path : str
            The path to the atlas directory containing the reference and label images.
        """
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

class SlideProcessor(Page):
    """
    Page for processing slides and selecting calibration points. This page allows the
    user to select slices and calibration points on the slides. It provides tools for
    adding, removing, and committing calibration points and target regions. The user
    can also switch between slides and adjust the annotation mode (point or rectangle).
    """

    def __init__(self, master, project):
        """
        Initialize the SlideProcessor page with the given master and project.

        Parameters
        ----------
        master : tk.Frame
            The parent window for the page.
        project : dict
            The project data containing slides and atlases.
        """
        super().__init__(master, project)
        self.header = "Select slices and calibration points."
        self.currSlide = None

        self.newPointX = self.newPointY = -1
        self.newTargetX = self.newTargetY = -1
        self.newTargetData = None

        # matplotlib rectangle selector for selecting slices
        self.slice_selector = mpl.widgets.RectangleSelector(
            self.slide_viewer.axes[0], 
            self.on_select,
            button=1,
            useblit=True,
            interactive=True
        )

    def create_widgets(self):
        """
        Create widgets for the SlideProcessor page. This includes:
        - Menu frame: Contains controls for annotation mode, buttons for adding/removing
          points and targets, and slide navigation.
        - Slide viewer: A matplotlib figure for displaying the current slide
        - Slide navigation: A combobox for selecting the current slide.
        """

        # menu
        self.menu_frame = tk.Frame(self)

        # annotation mode controls
        self.annotation_mode = tk.StringVar(
            master=self.menu_frame,
            value="point"
        )
        self.point_radio = ttk.Radiobutton(
            master=self.menu_frame,
            command=self.activate_point_mode,
            value="point",
            variable=self.annotation_mode,
            text='Add Calibration Points',
            style='Toolbutton'
        )
        self.rectangle_radio = ttk.Radiobutton(
            master=self.menu_frame,
            command=self.activate_rect_mode,
            value="rect",
            variable=self.annotation_mode,
            text="Select Slices",
            style='Toolbutton'
        )
        
        # menu buttons for adding/removing/clearing points and targets
        self.menu_buttons_frame = tk.Frame(self.menu_frame)
        self.remove_btn = ttk.Button(
            master=self.menu_buttons_frame,
            text='',
            command = self.remove,
            state='disabled'
        )
        self.commit_btn = ttk.Button(
            master=self.menu_buttons_frame,
            text='',
            command=self.commit,
            state='disabled'
        )
        self.clear_btn = ttk.Button(
            master=self.menu_buttons_frame,
            text='Clear uncommitted',
            command=self.clear,
            state='disabled'
        )
        # TODO: "clear all" button to clear all targets or points from current slide

        # slide navigation
        self.slide_nav_label = ttk.Label(self.menu_frame, text="Slide: ")
        self.curr_slide_var = tk.IntVar(master=self.menu_frame, value='1')
        self.slide_nav_combo = ttk.Combobox(
            master=self.menu_frame,
            values=[],
            state='readonly',
            textvariable=self.curr_slide_var,
        )
        self.slide_nav_combo.bind('<<ComboboxSelected>>', self.refresh)

        # slide viewer
        self.slides_frame = tk.Frame(self)
        self.slide_viewer = TkFigure(self.slides_frame, toolbar=True)

    def activate(self):
        """
        Activate the SlideProcessor page. This method sets up the initial state
        of the page, including the current slide and annotation mode. It also
        connects the click event to the slide viewer for adding calibration points
        and selecting slices. If the annotation mode is set to 'point', it activates
        point mode; if set to 'rect', it activates rectangle mode.
        """
        self.refresh() # update buttons, slideviewer
        if self.annotation_mode.get() == 'point':
            self.activate_point_mode()
        elif self.annotation_mode.get() == 'rect':
            self.activate_rect_mode()
        super().activate()

    def show_widgets(self):
        """
        Show the widgets for the SlideProcessor page. This method arranges the
        widgets in a grid layout and configures their appearance. It sets up the
        grid for the menu and slide viewer, and packs the widgets into their respective
        frames.
        """

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # show menu
        self.menu_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')
        self.point_radio.pack(side=tk.LEFT)
        self.rectangle_radio.pack(side=tk.LEFT)
        self.slide_nav_combo.config(
            values=[i+1 for i in range(len(self.slides))]
        )
        self.slide_nav_combo.pack(side=tk.RIGHT)
        self.slide_nav_label.pack(side=tk.RIGHT)

        self.menu_buttons_frame.pack()
        self.remove_btn.pack(side=tk.LEFT)
        self.commit_btn.pack(side=tk.LEFT)
        self.clear_btn.pack(side=tk.LEFT)

        # show slide viewer
        self.slides_frame.grid(row=1, column=0, sticky='nsew')
        self.slide_viewer.get_widget().pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    def show_slide(self, event=None):
        """
        Show the current slide in the slide viewer. This method updates the
        slide viewer with the current slide's image and draws rectangles for
        the targets and calibration points. It also highlights the current
        calibration points and targets with different colors.
        
        Parameters
        ----------
        event : tk.Event, optional
            The event that triggered the update (default is None).
        """
        #TODO: confirm that removing event=None does not break anything
        
        # clear the axes and show the current slide image
        self.slide_viewer.axes[0].cla()
        self.slide_viewer.axes[0].imshow(self.currSlide.get_img())
        
        # draw rectangles for targets
        for i,target in enumerate(self.currSlide.targets):
            edgecolor = COMMITTED_COLOR
            if i == self.currSlide.numTargets-1: edgecolor = REMOVABLE_COLOR
            self.slide_viewer.axes[0].add_patch(
                mpl.patches.Rectangle(
                    (target.x_offset, target.y_offset),
                    target.img_original.shape[1], 
                    target.img_original.shape[0],
                    edgecolor=edgecolor,
                    facecolor='none', 
                    lw=3
                )
            )
        
        # draw calibration points
        point_size = 10
        if self.currSlide.numCalibrationPoints > 0:
            points = np.array(self.currSlide.calibration_points)
            self.slide_viewer.axes[0].scatter(
                points[:-1,0], 
                points[:-1,1], 
                color=COMMITTED_COLOR, 
                s=point_size
            )
            self.slide_viewer.axes[0].scatter(
                points[-1,0], 
                points[-1,1], 
                color=REMOVABLE_COLOR, 
                s=point_size
            )
        if not (self.newPointX == -1 and self.newPointY == -1):
            self.slide_viewer.axes[0].scatter(
                self.newPointX, self.newPointY, 
                color=NEW_COLOR, 
                s=point_size
            )

        self.slide_viewer.update()

    def refresh(self, event=None):
        """
        Refresh the page by updating slide index, clearing uncommitted targets and points,
        and updating slide viewer and buttons.

        Parameters
        ----------
        event : tk.Event, optional
            The event that triggered the update (default is None).
        """
        self.currSlide = self.slides[self.get_index()]
        self.clear() # clear and show new slide image
        self.update_buttons() # update buttons

    def update_buttons(self):
        """
        Update the text and state of the buttons based on the current annotation mode
        and the current slide's targets and calibration points. This method enables or
        disables the remove, commit, and clear buttons based on whether there are
        targets or calibration points to add or remove.
        """
        mode = self.annotation_mode.get()
        if mode == 'rect':
            self.remove_btn.config(text="Remove Section")
            self.commit_btn.config(text="Add Section")
            canRemove = self.currSlide.numTargets > 0
            canAdd = self.newTargetData is not None
        elif mode == 'point':
            self.remove_btn.config(text="Remove Point")
            self.commit_btn.config(text="Add Point")
            canRemove = self.currSlide.numCalibrationPoints > 0
            canAdd = not self.newPointX==self.newPointY==-1
        else: return

        if canRemove:
            self.remove_btn.config(state='active')
        else:
            self.remove_btn.config(state='disabled')
        
        if canAdd:
            self.commit_btn.config(state='active')
            self.clear_btn.config(state='active')
        else:
            self.commit_btn.config(state='disabled')
            self.clear_btn.config(state='disabled')

    def on_select(self, click, release):
        """
        Callback for the rectangle selector. This method is called when the user
        selects a rectangle on the slide viewer in "rect" mode. If the selection
        is a valid rectangle (i.e., the start and end points are different), it
        updates the new target coordinates and data based on the selected rectangle.
        
        Parameters
        ----------
        click : mpl.backend_bases.MouseEvent
            The mouse event for the click action.
        release : mpl.backend_bases.MouseEvent
            The mouse event for the release action.
        """
        startX, startY = int(click.xdata), int(click.ydata)
        endX, endY = int(release.xdata), int(release.ydata)
        if startX==endX and startY==endY:
            self.newTargetX = -1
            self.newTargetY = -1
            self.newTargetData = None
        else:
            self.newTargetX = startX
            self.newTargetY = startY
            self.newTargetData = self.currSlide.get_img()[startY:endY, startX:endX]
        
        self.update_buttons()

    def on_click(self, event):
        """
        Callback for mouse click events on the slide viewer. This method is called
        when the user clicks on the slide viewer in "point" mode. If the click is within
        the axes, it updates the new point coordinates based on the click position.
        
        Parameters
        ----------
        event : mpl.backend_bases.MouseEvent
            The mouse event for the click action.
        """

        if event.inaxes is None: return
        x,y = int(event.xdata), int(event.ydata)
        if event.button == 1:
            self.newPointX = x
            self.newPointY = y

        self.update_buttons()
        self.show_slide() # TODO: speed up software by not redrawing the entire slide every time a point is added

    def activate_point_mode(self):
        """
        Activate point mode for adding calibration points. This method clears the
        current slide's uncommitted target and point data, connects click event for
        adding calibration points, disconnects the rectangle selector, and updates the
        buttons.
        """
        self.clear()
        self.slice_selector.set_active(False)
        self.click_event = self.slide_viewer.canvas.mpl_connect('button_press_event', self.on_click)
        self.update_buttons()

    def activate_rect_mode(self):
        """
        Activate rectangle mode for selecting slices. This method clears the
        current slide's uncommitted target and point data, connects the rectangle
        selector for selecting slices, disconnects the click event, and updates
        the buttons.
        """
        self.clear()
        self.slice_selector.set_active(True)
        self.slide_viewer.canvas.mpl_disconnect(self.click_event)
        self.update_buttons()

    def remove(self):
        """
        Remove the currently selected target or point based on the annotation mode.
        """

        mode = self.annotation_mode.get()
        if mode == 'rect':
            self.currSlide.remove_target()
        elif mode == 'point':
            self.currSlide.remove_calibration_point()
        else: return

        self.show_slide()
        self.update_buttons

    def commit(self):
        """
        Commit the current target or point based on the annotation mode.
        """

        mode = self.annotation_mode.get()
        if mode == 'rect':
            if self.newTargetData is None: return
            self.currSlide.add_target(
                self.newTargetX, 
                self.newTargetY,
                self.newTargetData 
            )
            self.newTargetData = None
            self.newTargetX = self.newTargetY = -1
            self.slice_selector.clear()
        elif mode == 'point':
            self.currSlide.add_calibration_point(
                [self.newPointX,self.newPointY]
            )
            self.newPointX = self.newPointY = -1
        else: return
        
        self.show_slide()
        self.update_buttons()

    def clear(self):
        """
        Clear the current slide's uncommitted target and point data and show the current
        slide image.
        """
        self.newTargetX = self.newTargetY = -1
        self.newPointX = self.newPointY = -1
        self.newTargetData = None
        self.slice_selector.clear()
        self.show_slide()

    def get_index(self):
        """
        Get the index of the current slide based on the selected value in the
        slide navigation combobox.

        Returns
        -------
        index : int
            The index of the current slide.
        """
        return self.curr_slide_var.get()-1

    def done(self):
        """
        Finalize the SlideProcessor page's actions. This method checks that each slide
        has at least one target and exactly three calibration points. If any slide does
        not meet these criteria, it raises an exception with an error message. It also
        saves the target coordinates and calibration points in text files, and saves the
        target images in the project folder.
        
        Raises
        -------
        Exception
            If any slide does not have at least one target or exactly three calibration points.
        """
        # TODO: if no targets selected, show warning and ask if user wants to use entire image as target, 
        # ^maybe also have option to just skip this image?

        for i,slide in enumerate(self.slides):
            e = None
            if slide.numTargets < 1: 
                e = Exception(f"No targets selected for slide #{i+1}")
            
            if slide.numCalibrationPoints != 3:
                e = Exception(f"Slide #{i+1} must have exactly 3 calibration points, found {slide.numCalibrationPoints}")
            else:
                # reorder calibration points so that first point is top left,
                # second is top right, and third is bottom left
                slide.calibration_points.sort()
                slide.calibration_points[1:] = sorted(
                    slide.calibration_points[1:], 
                    key=lambda point: point[1]
                )

            # if there was an error, set the current slide to the one with the error
            # and show the error message
            if e is not None:
                self.curr_slide_var.set(i+1)
                # TODO: should also set annotation mode to the one necessary
                self.refresh()
                tk.messagebox.showerror(
                    title="Error",
                    message=str(e)
                )
                raise e

        # save target coordinates in a text file
        with open(os.path.join(self.project.folder, 'target_coordinates.txt'), 'w') as f:
            f.write("slide#_target# : X Y\n")
            for si, slide in enumerate(self.slides):
                for ti, target in enumerate(slide.targets):
                    f.write(f"{get_filename(si, ti)} : {target.x_offset} {target.y_offset}\n")

        # save calibration points in a text file
        with open(os.path.join(self.project.folder, 'calibration_points.txt'), 'w') as f:
            f.write("slide# : X Y\n")
            for si, slide in enumerate(self.slides):
                for point in slide.calibration_points:
                    f.write(f"{si} : {point[0]} {point[1]}\n")
        
        # save target images in the project folder
        for si, slide in enumerate(self.slides):
            for ti, target in enumerate(slide.targets):
                filename = get_filename(si, ti)+'.png'
                ski.io.imsave(os.path.join(self.project.folder, filename),target.img_original)

        super().done()

    def cancel(self):
        """
        Cancel the actions on the SlideProcessor page. This method clears the
        current slide's uncommitted target and point data, disconnects the click
        event and rectangle selector, and calls the parent class's cancel method
        to finalize the page's actions.
        """
        self.slides.clear()
        super().cancel()

class TargetProcessor(Page):
    """
    Page for selecting landmark points and adjusting affine transformations.
    This page allows the user to select landmark points on the atlas and adjust
    affine transformations based on the selected points. It provides tools for
    adding, removing, and committing landmark points, as well as adjusting the
    affine transformations using rotation and translation scales.
    """

    # TODO: add feature to select between rotation/translation control and landmark annotation mode
    # during rotation/translation, use low resolution atlas images

    def __init__(self, master, project):
        super().__init__(master, project)
        self.header = "Select landmark points and adjust affine."
        self.currSlide = None
        self.currTarget = None
        self.new_points = [[],[]]
        self.point_size = 4

    def create_widgets(self):
        """
        Create widgets for the TargetProcessor page. This includes:
        - Menu frame: Contains controls for slide and target navigation, buttons for
          removing and committing points, and clearing uncommitted points.
        - Slice frame: Contains the slice viewer for displaying the atlas images
          and the rotation and translation controls.
        - Parameter settings frame: Contains controls for adjusting parameters for
          automatic alignment, including basic and advanced parameter settings.
        """
        
        # menu frame with slide and target navigation, buttons, and controls
        self.menu_frame = tk.Frame(self)

        # slide navigation
        self.slide_nav_label = ttk.Label(self.menu_frame, text="Slide: ")
        self.curr_slide_var = tk.IntVar(master=self.menu_frame, value='1')
        self.slide_nav_combo = ttk.Combobox(
            master=self.menu_frame,
            values=[],
            state='readonly',
            textvariable=self.curr_slide_var,
        )
        self.slide_nav_combo.bind('<<ComboboxSelected>>', self.switch_slides)

        # target navigation
        self.target_nav_label = ttk.Label(self.menu_frame, text="Target: ")
        self.curr_target_var = tk.IntVar(master=self.menu_frame, value='1')
        self.target_nav_combo = ttk.Combobox(
            master=self.menu_frame,
            values=[],
            state='readonly',
            textvariable=self.curr_target_var,
        )
        self.target_nav_combo.bind('<<ComboboxSelected>>', self.update)

        # landmark annotation controls
        self.menu_buttons_frame = tk.Frame(self.menu_frame)
        self.remove_btn = ttk.Button(
            master=self.menu_buttons_frame,
            text='Remove Point',
            command = self.remove,
            state='disabled'
        )
        self.commit_btn = ttk.Button(
            master=self.menu_buttons_frame,
            text='Add Point',
            command=self.commit,
            state='disabled'
        )
        self.clear_btn = ttk.Button(
            master=self.menu_buttons_frame,
            text='Clear uncommitted',
            command=self.clear,
            state='disabled'
        )

        # slice frame with viewer and controls
        self.slice_frame = tk.Frame(self)

        # slice viewer for displaying atlas images
        self.figure_frame = tk.Frame(self.slice_frame)
        self.slice_viewer = TkFigure(self.figure_frame, num_cols=2, toolbar=True)
        self.click_event = self.slice_viewer.canvas.mpl_connect('button_press_event', self.on_click)

        # rotation controls
        self.rotation_frame = tk.Frame(self.slice_frame)
        self.thetas = [tk.IntVar(self.rotation_frame, value=0) for i in range(3)]
        self.x_rotation_scale = ttk.Scale(
            master=self.rotation_frame, 
            from_=90, to=-90, 
            orient='vertical', 
            variable=self.thetas[2],
            command=self.show_atlas
        )
        self.y_rotation_scale = ttk.Scale(
            master=self.rotation_frame, 
            from_=90, to=-90, 
            orient='vertical', 
            variable=self.thetas[1],
            command=self.show_atlas
        )
        self.z_rotation_scale = ttk.Scale(
            master=self.rotation_frame, 
            from_=180, to=-180, 
            orient='vertical', 
            variable=self.thetas[0],
            command=self.show_atlas
        )
        self.rotation_labels = [ttk.Label(
                                    master=self.rotation_frame,
                                    text=self.thetas[i].get()
                                ) for i in range(3)]

        # translation controls
        self.translation_frame = tk.Frame(self.slice_frame)
        self.translation = tk.DoubleVar(self.translation_frame, value=0)
        self.translation_scale = ttk.Scale(
            master=self.translation_frame,
            orient='horizontal',
            variable=self.translation,
            command=self.show_atlas
        )
        self.translation_label = ttk.Label(
            master=self.translation_frame,
            text=self.translation.get()
        )

        # paramater settings
        self.params_frame = tk.Frame(self)
        self.params_label = ttk.Label(
            self.params_frame,
            text="Adjust parameters for automatic alignment"
        )
        self.params_save_btn = ttk.Button(
            master=self.params_frame,
            text='Save parameters for slice',
            command=self.save_params
        )
        
        # basic parameter settings
        self.basic_frame = tk.Frame(self.params_frame, pady=10)
        self.basic_label = ttk.Label(
            master=self.basic_frame,
            text="Basic"
        )
        self.basic_param_label = ttk.Label(
            self.basic_frame, 
            text="Speed: "
        )
        self.basic_options = [
            'very slow 1-2 hrs/sample',
            'slow 15-30 min/sample', 
            'medium 3-5 min/sample', 
            'fast 20-30 sec/sample', 
            'skip automatic alignment' 
        ]
        self.basic_combo = ttk.Combobox(
            master=self.basic_frame,
            values = self.basic_options,
            state='readonly'
        )
        self.basic_combo.bind('<<ComboboxSelected>>', self.basic_to_advanced)
        self.basic_combo.set(self.basic_options[2])
        
        # advanced parameter settings
        self.advanced_frame = tk.Frame(self.params_frame)
        self.advanced_label = ttk.Label(
            master=self.advanced_frame,
            text="Advanced"
        )
        self.advanced_params_frame = tk.Frame(self.advanced_frame)
        self.param_vars, self.advanced_entries, self.advanced_param_labels = {}, {}, {}
        val_cmd = self.register(self.isFloat)
        for key, value in DEFAULT_STALIGN_PARAMS.items():
            self.param_vars[key] = tk.StringVar(master=self.advanced_params_frame, value=value)
            self.advanced_param_labels[key] = ttk.Label(master=self.advanced_params_frame, text=f'{key}:')
            self.advanced_entries[key] = ttk.Entry(
                master=self.advanced_params_frame, 
                textvariable=self.param_vars[key],
                validate='key',
                validatecommand=(val_cmd,'%P')
            )

    def activate(self):
        """
        Activate the TargetProcessor page. This method sets up the initial state
        of the page, including the current slide and target. It also updates the
        atlas images and sets the pixel dimensions for the target images. It
        configures the translation scale based on the atlas pixel locations.
        """

        atlas = self.atlases[DSR]
        for slide in self.slides:
            for target in slide.targets:
                self.update_img_estim(target)
                target.img_estim.set_pix_dim(atlas.pix_dim[1:]*ALPHA)
                target.img_estim.set_pix_loc()

        self.translation_scale.config(
            from_=self.atlases[DSR].pix_loc[0][0],
            to_=self.atlases[DSR].pix_loc[0][-1]
        )

        super().activate()

    def show_widgets(self):
        """
        Show the widgets for the TargetProcessor page. This method arranges the
        widgets in a grid layout and configures their appearance. It sets up the
        grid for the menu, slice viewer, rotation and translation controls, and
        parameter settings. It also packs the widgets into their respective frames.
        """
        
        self.update()
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.menu_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')
        self.slice_frame.grid(row=1, column=0, sticky='nsew')
        self.slice_frame.grid_rowconfigure(0, weight=1)
        self.slice_frame.grid_columnconfigure(0, weight=1)
        self.slice_frame.grid_columnconfigure(1, weight=1)

        self.slide_nav_label.pack(side=tk.LEFT)
        self.slide_nav_combo.pack(side=tk.LEFT)
        
        self.target_nav_combo.pack(side=tk.RIGHT)
        self.target_nav_label.pack(side=tk.RIGHT)

        self.menu_buttons_frame.pack()
        self.remove_btn.pack(side=tk.LEFT)
        self.commit_btn.pack(side=tk.LEFT)
        self.clear_btn.pack(side=tk.LEFT)

        self.figure_frame.grid(
            row=0, 
            column=0, 
            columnspan=2, 
            sticky='nsew'
        )
        self.slice_viewer.get_widget().pack(expand=True, fill=tk.BOTH)
        
        self.rotation_frame.grid(row=0, column=2, sticky='nsew')
        self.rotation_frame.grid_rowconfigure(0, weight=1)
        self.x_rotation_scale.grid(row=0, column=0, sticky='nsew')
        self.y_rotation_scale.grid(row=0, column=1, sticky='nsew')
        self.z_rotation_scale.grid(row=0, column=2, sticky='nsew')
        self.rotation_labels[2].grid(row=1, column=0)
        self.rotation_labels[1].grid(row=1, column=1)
        self.rotation_labels[0].grid(row=1, column=2)
        
        self.translation_frame.grid(row=1,column=1, sticky='nsew')
        self.translation_scale.pack(fill=tk.X)
        self.translation_label.pack()

        # show prameter settings
        self.params_frame.grid(row=1, column=1, sticky='nsew')
        self.params_label.pack()
        self.params_save_btn.pack(side=tk.BOTTOM, anchor='se')

        self.basic_frame.pack(fill=tk.X)
        self.basic_label.pack()
        self.basic_param_label.pack(side=tk.LEFT, anchor='nw')
        self.basic_combo.pack(side=tk.RIGHT, anchor='ne', expand=True, fill=tk.X)

        self.advanced_frame.pack(fill=tk.X)
        self.advanced_label.pack()
        self.advanced_params_frame.pack()
        self.advanced_params_frame.columnconfigure(1, weight=1)
        for i,key in enumerate(self.advanced_entries):
            label = self.advanced_param_labels[key]
            entry = self.advanced_entries[key]
            label.grid(row=i, column=0)
            entry.grid(row=i, column=1, sticky='ew')

    def update(self, event=None):
        """
        Update the current slide and target based on the selected values in the
        slide and target navigation comboboxes. This method retrieves the current
        slide and target based on the selected indices, updates the slide and target
        navigation comboboxes, and sets the current target's theta values and
        translation value. It also resets the new points and updates the target
        and atlas images in the slice viewer.
        
        Parameters
        ----------
        event : tk.Event, optional
            The event that triggered the update (default is None).
        """
        self.currSlide = self.slides[self.get_slide_index()]
        self.slide_nav_combo.config(
            values=[i+1 for i in range(len(self.slides))]
        )

        self.currTarget = self.currSlide.targets[self.get_target_index()]
        self.target_nav_combo.config(
            values=[i+1 for i in range(self.currSlide.numTargets)]
        )

        if (self.currTarget.thetas == np.array([0,0,0])).all():
            n = 0
            thetas_avg = np.array([0,0,0])
            for target in self.currSlide.targets:
                if (target.thetas != np.array([0,0,0])).any():
                    thetas_avg += target.thetas
                    n += 1
            if n > 0: self.currTarget.thetas = np.divide(thetas_avg,n).astype('int64')

        for i in range(3): self.thetas[i].set(self.currTarget.thetas[i])
        self.translation.set(self.currTarget.T_estim[0])

        self.new_points = [[],[]] # reset new points

        self.show_target()
        self.show_atlas()
        self.update_buttons()

        curr_params = self.currTarget.stalign_params
        for key,var in self.param_vars.items():
            var.set(curr_params[key])
        
        self.set_basic()

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
        self.curr_target_var.set(1) # reset target index to 1
        self.update()

    def show_target(self):
        """
        Show the current target image in the slice viewer. This method clears
        the axes for the target image, sets the title, and displays the target
        image with the appropriate colormap. It also highlights the new point
        and the committed and removable landmark points with different colors.
        """
        # show target image, show landmark points
        self.slice_viewer.axes[0].cla()
        self.slice_viewer.axes[0].set_axis_off()
        self.slice_viewer.axes[0].set_title(f"Slide #{self.get_slide_index()+1}\nSlice #{self.get_target_index()+1}")
        self.slice_viewer.axes[0].imshow(self.currTarget.img, cmap='Greys')
        
        point = self.new_points[0]
        if len(point) == 2: 
            self.slice_viewer.axes[0].scatter(
                point[1], point[0], 
                color=NEW_COLOR,
                s=self.point_size
            )

        landmarks = np.array(self.currTarget.landmarks['target'])
        if len(landmarks) > 0:
            self.slice_viewer.axes[0].scatter(
                landmarks[:-1, 1], landmarks[:-1, 0],
                color=COMMITTED_COLOR,
                s=self.point_size
            )
            self.slice_viewer.axes[0].scatter(
                landmarks[-1, 1], landmarks[-1, 0],
                color=REMOVABLE_COLOR,
                s=self.point_size
            )

        self.slice_viewer.update()

    def update_img_estim(self, target):
        """
        Update the estimated image for the target based on the current affine
        transformation parameters. This method retrieves the atlas for the current
        target, applies the affine transformation to the atlas pixel locations,
        and transforms the slice image using the target's affine transformation
        parameters. It then updates the target's estimated image with the transformed
        slice image.
        
        Parameters
        ----------
        target : Target
            The target for which to update the estimated image.
        """

        atlas = self.atlases[DSR]
        
        xE = [ALPHA*x for x in atlas.pix_loc]
        XE = np.stack(np.meshgrid(np.zeros(1),xE[1],xE[2],indexing='ij'),-1)
        L,T = target.get_LT()
        slice_transformed = (L @ XE[...,None])[...,0] + T
        slice_img = atlas.get_img(slice_transformed)
        
        target.img_estim.load_img(slice_img)

    def show_atlas(self, event=None):
        """
        Show the atlas image in the slice viewer. This method clears the axes for
        the atlas image, sets the title, and displays the atlas image with the
        appropriate colormap. It also highlights the new point and the committed
        and removable landmark points with different colors. It updates the affine
        transformation parameters based on the current rotation and translation
        values, and applies the affine transformation to the atlas pixel locations.
        
        Parameters
        ----------
        event : tk.Event, optional
            The event that triggered the update (default is None).
        """
        self.slice_viewer.axes[1].cla()
        self.slice_viewer.axes[1].set_title("Atlas")
        self.slice_viewer.axes[1].set_axis_off()

        for i in range(3): 
            self.currTarget.thetas[i] = self.thetas[i].get()
            self.rotation_labels[i].config(text=self.thetas[i].get())

        self.currTarget.T_estim[0] = self.translation.get()
        self.translation_label.config(text=self.translation.get())

        self.update_img_estim(self.currTarget)
        self.slice_viewer.axes[1].imshow(self.currTarget.img_estim.get_img(), cmap='Grays')

        point = self.new_points[1]
        if len(point) == 2: 
            self.slice_viewer.axes[1].scatter(
                point[1], point[0], 
                color='red',
                s=self.point_size
            )

        landmarks = np.array(self.currTarget.landmarks['atlas'])
        if len(landmarks) > 0:
            self.slice_viewer.axes[1].scatter(
                landmarks[:-1, 1], landmarks[:-1, 0],
                color=COMMITTED_COLOR,
                s=self.point_size
            )
            self.slice_viewer.axes[1].scatter(
                landmarks[-1, 1], landmarks[-1, 0],
                color=REMOVABLE_COLOR,
                s=self.point_size
            )
        
        self.slice_viewer.update()

    def update_buttons(self):
        """
        Update the state of the buttons based on the current target's landmarks
        and the new points selected by the user. This method enables or disables
        the remove, commit, and clear buttons based on whether there are landmarks
        to remove, new points to add, or existing points to clear. It also ensures
        that the buttons are only active when there are changes to save.
        """
        #TODO: make save parameters button only active if changes to save
        #TODO: add options to save stalign params to slice, slide, or all

        canRemove = self.currTarget.num_landmarks > 0
        canAdd = len(self.new_points[0]) == 2 and len(self.new_points[1]) == 2
        canClear = len(self.new_points[0]) == 2 or len(self.new_points[1]) == 2

        if canRemove:
            self.remove_btn.config(state='active')
        else:
            self.remove_btn.config(state='disabled')
        
        if canAdd:
            self.commit_btn.config(state='active')
        else:
            self.commit_btn.config(state='disabled')
        
        if canClear:
            self.clear_btn.config(state='active')
        else:
            self.clear_btn.config(state='disabled')

    def on_click(self, event):
        """
        Callback for mouse click events on the slice viewer. This method is called
        when the user clicks on the slice viewer to select landmark points. It checks
        if the click is within the axes, retrieves the new point coordinates based on
        the click position, and updates the new points for the target and atlas images.
        
        Parameters
        ----------
        event : tk.Event
            The event that triggered the update.
        """
        if event.inaxes is None: return

        new_x, new_y = int(event.xdata), int(event.ydata)
        if event.inaxes is self.slice_viewer.axes[0]:
            # clicked on target
            self.new_points[0] = [new_y, new_x]
            self.show_target()
        elif event.inaxes is self.slice_viewer.axes[1]:
            # clicked on atlas
            self.new_points[1] = [new_y, new_x]
            self.show_atlas()
        
        self.update_buttons()

    def remove(self):
        """
        Remove the currently selected landmark points from the current target.
        This method checks if the current target has any landmarks to remove. If
        there are landmarks, it removes the last landmark point from both the target
        and atlas images, updates the new points, and refreshes the display.
        """
        self.currTarget.remove_landmarks()
        self.update()

    def commit(self):
        """
        Commit the new landmark points to the current target. This method checks if
        there are new points selected for both the target and atlas images. If there
        are new points, it adds the new points to the current target's landmarks for
        both the target and atlas images, clears the new points, and updates the display.
        """

        self.currTarget.add_landmarks(self.new_points[0], self.new_points[1])
        self.new_points = [[],[]]
        self.update()

    def clear(self):
        """
        Clear the new points selected for the target and atlas images. This method
        resets the new points to empty lists, updates the display, and refreshes the
        buttons to reflect the cleared state.
        """

        self.new_points = [[],[]]
        self.update()
    
    def save_params(self):
        """
        Save the current parameters for the current target. This method retrieves
        the parameter values from the advanced entries, updates the current target's
        parameters with the new values, and sets the basic settings based on the
        current target's parameters. It also prints a confirmation message indicating
        that the parameters have been saved.
        """
        for key, value in self.param_vars.items():
            self.currTarget.set_param(key, float(value.get()))
        self.set_basic()
        # confirm
        print("parameters saved!")

    def basic_to_advanced(self, event=None):
        """
        Convert the basic settings selected in the combobox to advanced parameters.
        This method retrieves the selected basic setting from the combobox, resets
        the advanced parameters to their default values, and sets the iterations
        based on the selected speed setting. It updates the advanced entries with
        the new values and prints a confirmation message indicating that the parameters
        have been reset to the defaults.

        Parameters
        ----------
        event : tk.Event, optional
            The event that triggered the update (default is None).
        """

        # reset params to defaults
        for key, var in self.param_vars.items():
            var.set(DEFAULT_STALIGN_PARAMS[key])
        
        # set iterations based on speed setting
        speed = self.basic_combo.get()
        if "very slow" in speed:
            self.param_vars['iterations'].set('2000')
        elif "slow" in speed:
            self.param_vars['iterations'].set('500')
        elif "medium" in speed:
            self.param_vars['iterations'].set('100')
        elif "fast" in speed:
            self.param_vars['iterations'].set('10')
        else:
            self.param_vars['iterations'].set('1') #TODO: ensure STalign doesn't explod when given 0 iterations

    def set_basic(self):
        """
        Set the basic settings based on the current target's parameters.
        This method checks the current target's parameters and updates the basic
        settings combobox to reflect the estimated time for the selected number of
        iterations. If the parameters do not match the default values, it sets the
        basic settings to "Advanced settings estimated X" where X is the estimated
        time based on the number of iterations. If the parameters match the default
        values, it sets the basic settings to one of the predefined options based on
        the number of iterations.
        """
        num_iterations = float(self.param_vars['iterations'].get())
        
        for key, var in self.param_vars.items():
            if key == 'iterations': continue
            if float(var.get()) != DEFAULT_STALIGN_PARAMS[key]:
                self.basic_combo.set(f"Advanced settings estimated {1/24*num_iterations}")
                return
        
        if num_iterations == 2000: self.basic_combo.set(self.basic_options[0])
        elif num_iterations == 500: self.basic_combo.set(self.basic_options[1])
        elif num_iterations == 100: self.basic_combo.set(self.basic_options[2])
        elif num_iterations == 10: self.basic_combo.set(self.basic_options[3])
        elif num_iterations == 1: self.basic_combo.set(self.basic_options[4])
        else:
            self.basic_combo.set(f"Advanced settings estimated {2.5*num_iterations}") 

    def done(self):
        """
        Finalize the TargetProcessor page's actions. This method uses the atlas
        image estimation to estimate the pixel dimensions for each target,
        creates folders for each target, and writes the affine parameters, landmark
        points, and stalign parameters to text files in the respective target folders.
        """
        
        # estimate pixel dimensions
        for si, slide in enumerate(self.slides):
            slide.estimate_pix_dim()
            for ti,target in enumerate(slide.targets):
                folder = os.path.join(
                    self.project.folder, 
                    get_folder(si, ti, self.project.stalign_iterations)
                )
                os.mkdir(folder)

                with open(os.path.join(folder, 'settings.txt'), 'w') as f:
                    # write affine parameters
                    f.write("AFFINE\n")
                    f.write(f"rotations : {target.thetas[0]} {target.thetas[1]} {target.thetas[2]}\n")
                    f.write(f"translation : {target.T_estim[0]} {target.T_estim[1]} {target.T_estim[2]}\n")
                    f.write("\n")

                    # write landmark points
                    f.write("LANDMARKS\n")
                    f.write("target point: atlas point\n")
                    for i in range(target.num_landmarks):
                        target_pt = target.landmarks['target'][i]
                        atlas_pt = target.landmarks['atlas'][i]
                        f.write(f"{target_pt[0]} {target_pt[1]} : {atlas_pt[0]} {atlas_pt[1]}\n")
                    f.write("\n")

                    # write stalign parameters
                    f.write("PARAMETERS\n")
                    f.write("parameter : value\n")
                    for key, value in target.stalign_params.items():
                        f.write(f"{key} : {value}\n")
        
        super().done()

    def cancel(self):
        """
        Cancel the actions on the TargetProcessor page. This method clears the
        current target's affine estimation and landmark points, resets the parameters,
        and calls the parent class's cancel method to finalize the page's actions.
        """

        # clear affine, landmark points, and stalign parameters
        for slide in self.slides:
            for target in slide.targets:
                target.set_param() # reset params
                target.thetas = np.array([0, 0, 0])
                target.T_estim = np.array([0, 0, 0])
                target.img_estim = Image()
                for i in range(target.num_landmarks): target.remove_landmarks()
        super().cancel()
    
    def isFloat(self, str):
        """
        Check if a string can be converted to a float.

        Parameters
        ----------
        str : str
            The string to check.
        
        Returns
        -------
        bool
            True if the string can be converted to a float, False otherwise.
        """
        try:
            float(str)
            return True
        except ValueError:
            return False

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

class STalignRunner(Page):
    """
    Page for running STalign and viewing results. This page runs 
    STalign, showing a progress bar, and then displays results once
    completed. It also saves graphs related to STalign runtime and 
    error tracking.
    """

    def __init__(self, master, project):
        super().__init__(master, project)
        self.header = "Running STalign."
    
    def activate(self):
        """
        Activate the STalignRunner page. This method calls 
        `estimate_time` to estimate the duration of STalign and
        configure the progress bar and labels accordingly.
        """
        # TODO: if all skipped -> immediately generate segmentations 
        # and call done()
        self.estimate_time()
        super().activate()

    def estimate_time(self):
        """
        Estimate duration of STalign for all targets. This method
        totals up the iterations for all planned STalign runs and
        calculates the duration of STalign my assuming each iteration
        takes 3 seconds. It also configures the progress bar and 
        text label with this information.
        """

        totalIterations = 0
        for slide in self.slides:
            for target in slide.targets:
                numIt = target.stalign_params['iterations']
                totalIterations += numIt
        self.progress_bar.config(maximum=totalIterations)

        time_sec = 3*totalIterations # ~3 sec/iteration
        time_str = STalignRunner.seconds_to_string(time_sec)

        label_txt = f'Estimated Duration: {time_str}'
        self.info_label.config(text=label_txt)

    def seconds_to_string(s):
        """
        Helper method that creates a verbose string describing a time
        duration given in seconds

        Parameters
        ----------
        s : int
            The time duration in seconds
        
        Returns
        -------
        output : str
            A verbose string that describes the time duration in days,
            hours, minutes, and seconds
        """
        units = {
            "day":24*60*60,
            "hour":60*60,
            "minute":60,
            "second":1
        }
        output_dict = {
            "day":0,
            "hour":0,
            "minute":0,
            "second":0
        }

        for unit,duration in units.items():
            output_dict[unit] = int(s//duration)
            s = s % duration
        
        output = [f'{value} {unit}(s)' for unit,value in output_dict.items() if value != 0]
        return " ".join(output)

    def create_widgets(self):
        """
        Create the widgets for this page. This includes:
        - Info Label: Displays information regarding time left, which
        target and slice is currently being aligned, and completion status
        - Progress Bar: Displays progress in STalign alignment
        - Results Frame: Contains figure displaying results along with
        navigation controls
        """
        self.info_label = ttk.Label(
            master=self,
        )

        self.start_btn = ttk.Button(
            master=self,
            command=self.run,
            text='Run'
        )

        self.progress_bar = ttk.Progressbar(
            master=self,
            mode='determinate',
            orient='horizontal',
            value=0
        )

        self.results_viewer = tk.Frame(self)
        self.create_result_viewer()

    def show_widgets(self):
        """
        Show the widgets. This method packs the widgets on the page.
        Of note, the Results Frame is not packed, but it's components
        are. This allows the results to be easily displayed after STalign
        completion by simply packing the Results Frame and hiding the 
        progress bar.
        """
        self.info_label.pack()
        self.start_btn.pack()
        self.show_result_viewer()
        
    def process_points(self, target):
        """
        Helper function for processing landmark points and returning
        processed points. This method converts the 2D landmarks for the
        atlas and target that are stored in the reference space of 
        the matplotlib figure and converts them to the reference 
        space of the atlas and target respectively.

        Parameters
        ----------
        target : Target
            The target whose points we want to process
        
        Returns
        -------
        processed : dict
            The processed points stored in a dictionary with keys "target"
            and "atlas"
        """
        if target.num_landmarks > 0:
            points_target_pix = np.array(target.landmarks['target'])
            points_atlas_pix = np.array(target.landmarks['atlas'])
            
            atlas = self.atlases[DSR]
            xE = [ALPHA*x for x in atlas.pix_loc]
            XE = np.stack(np.meshgrid(np.zeros(1),xE[1],xE[2],indexing='ij'),-1)
            L,T = target.get_LT()
            slice_pts = (L @ XE[...,None])[...,0] + T

            points_atlas = slice_pts[0, points_atlas_pix[:,0], points_atlas_pix[:,1]]
            points_target = points_target_pix * target.pix_dim + [target.pix_loc[0][0], target.pix_loc[1][0]]
            points_target = np.insert(points_target, 0, 0, axis=1)
            return {"target": points_target, "atlas": points_atlas}
        else:
            return {"target": None, "atlas": None}  

    def get_transform(self, target, device, figure):
        """
        Get the transform using STalign for a given target. This method
        runs STalign for the provided target, using parameters stored
        as class attributes of the target.

        Parameters
        ----------
        target : Target
            The target to be aligned using STalign.
        device : str
            The device to perform STalign on (i.e. 'cpu' or 'cuda')
        
        Returns
        -------
        transform : dict
            A dictionary containing the results of STalign alignment. 
            These results include the affine transform and the velocity
            graph mapping the target to the atlas.
        """
        # processing points
        processed_points = self.process_points(target)

        # processing input affine
        L,T = target.get_LT()
        L = np.linalg.inv(L)
        T = -T

        # final target and atlas processing
        xI = self.atlases[FSR].pix_loc
        I = self.atlases[FSR].img
        I = I[None] / np.mean(np.abs(I), keepdims=True)
        I = np.concatenate((I, (I-np.mean(I))**2))
        xJ = target.pix_loc
        J = target.img
        J = J[None] / np.mean(np.abs(J))

        

        transform, errors = LDDMM_3D_LBFGS(
            xI,I,xJ,J,
            T=T,L=L,
            device=device,
            pointsI=processed_points["atlas"], # DO NOT CHANGE
            pointsJ=processed_points["target"], # DO NOT CHANGE
            nt=int(target.stalign_params['timesteps']),
            niter=int(target.stalign_params['iterations']),
            sigmaM=target.stalign_params['sigmaM'],
            sigmaP=target.stalign_params['sigmaP'],
            sigmaR=target.stalign_params['sigmaR'],
            a=target.stalign_params['resolution'],
            progress_bar=self.progress_bar,
            figure=figure
        )

        return transform, errors

    def get_segmentation(self, target):
        """
        Get the segmentation of the target using the alignment created
        by STalign. This method applies the transform (provided by STalign)
        onto the labels atlas (a pre-segmented atlas corresponding to the
        reference atlas) to generate a segmentation mask for the target image.

        Parameters
        ----------
        target : Target
            The target whose segmentation is being requested.
        
        Returns
        -------
        segmentation : ndarray
            A numpy array representing the segmentation mask of the Target
            image.
        """
        transform = target.transform
        At = transform['A']
        v = transform['v']
        xv = transform['xv']

        atlas = self.atlases[FSL]
        vol = atlas.img
        dxL = atlas.pix_dim
        nL = atlas.shape
        xL = [np.arange(n)*d - (n-1)*d/2 for n,d in zip(nL,dxL)]

        # next chose points to sample on
        XJ = np.stack(np.meshgrid(
            np.zeros(1),
            target.pix_loc[0],
            target.pix_loc[1],
            indexing='ij'),-1)

        tform = STalign.build_transform3D(
            xv,v,At,
            direction='b',
            XJ=torch.tensor(XJ,device=At.device)
        )

        segmentation = STalign.interp3D(
            xL,
            torch.tensor(vol[None].astype(np.float64),dtype=torch.float64,device=tform.device),
            tform.permute(-1,0,1,2),
            mode='nearest'
        )[0,0].cpu().int().numpy()
        
        return segmentation

    def run(self):
        """
        Run STalign on all the targets. This method iterates through
        all the targets, gets the transform by running STalign,
        gets the segmentation for the target, and saves results in the 
        folder. Finally, it displays the results.
        """
        print('running!')
        self.start_btn.pack_forget()
        self.progress_bar.pack()
        # specify device
        if torch.cuda.is_available():
            device = 'cuda'
        else:
            device = 'cpu'
        
        stalign_window = tk.Toplevel(self)
        figure = TkFigure(stalign_window, num_cols=0, num_rows=0)
        figure.get_widget().pack(expand=True, fill=tk.BOTH)

        for sn,slide in enumerate(self.slides):
            for tn,target in enumerate(slide.targets):
                label_txt = f'Running STalign on Slice #{tn+1} of Slide #{sn+1}'
                print(label_txt)
                self.info_label.config(text=label_txt)
                self.update()
                figure.clear()
                
                target.transform, errors = self.get_transform(
                    target, 
                    device, 
                    figure
                )
                target.seg_stalign = self.get_segmentation(target)

                # saving results
                folder_path = os.path.join(
                    self.project.folder, 
                    get_folder(sn, tn, self.project.stalign_iterations)
                )

                # save figure
                figure.savefig(os.path.join(folder_path, 'stalign_graph.png'))

                # save transform
                with open(os.path.join(folder_path, 'stalign_transform.pkl'), 'wb') as f:
                    pickle.dump(target.transform, f)
                
                # save errors
                with open(os.path.join(folder_path, 'stalign_errors.pkl'), 'wb') as f:
                    pickle.dump(errors, f)
                
                # save segmentation
                folder = get_folder(sn, tn, self.project.stalign_iterations)
                np.save(
                    os.path.join(
                        folder_path,
                        "stalign_segmentation.npy"
                    ),
                    target.seg_stalign
                )
                
                # save outlines TODO: fix using figure_generation.ipynb on windows 1
                ski.io.imsave(
                    os.path.join(
                        folder_path,
                        "stalign_outlines.png"
                    ),
                    (255*target.get_img(seg="stalign")).astype(np.uint8)
                )

        self.info_label.config(text="Done!")
        stalign_window.destroy()
        self.progress_bar.pack_forget()
        self.show_results()
        self.update()

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
        seg_img = self.currTarget.get_img(seg="stalign")
        self.slice_viewer.axes[0].imshow(seg_img)
        self.slice_viewer.update()

    def show_results(self):
        """
        Show the results frame. This method updates the figure to display
        the current target's results, ensures the navigation controls are 
        correctly configured, and packs the results frame so that it's 
        visible.
        """

        self.currSlide = None
        self.currTarget = None
        self.update_result_viewer()

        self.slide_nav_combo.config(
            values=[i+1 for i in range(len(self.slides))]
        )
        self.results_viewer.pack(expand=True, fill=tk.BOTH)
    
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

    def done(self):
        """
        Finalize the STalignRunner page's actions. This method checks
        that each target has an estimated segmentation. If not, it 
        raises an Exception and informs the user to run STalign before
        advancing.
        """

        if self.slides[0].targets[0].transform is None:
            raise Exception("ERROR! Must Run STalign before advancing")
        super().done()
    
    def cancel(self):
        """
        Cancel the actions on the STalignRunner page. This method clears
        the results of STalign and hides the results frame.
        """

        self.results_viewer.pack_forget()
        for slide in self.slides:
            for target in slide.targets:
                target.transform = None
                target.seg_stalign = None
        self.project.stalign_iterations += 1
        super().cancel()

class VisuAlignRunner(Page):
    """
    Page for running VisuAlign. This page prepares the data
    for VisuAlign, including creating a NIfTI file with the
    segmentation stack and a JSON file with the necessary
    information for VisuAlign. It also provides instructions
    for the user to follow in order to perform the alignment
    in VisuAlign and save the results.
    """
    def __init__(self, master, project):
        super().__init__(master, project)
        self.header = "Running VisuAlign."

    def activate(self):
        """
        Activate the VisuAlignRunner page. This method prepares
        the data for VisuAlign by creating a NIfTI file with the
        segmentation stack and a JSON file with the necessary
        information for VisuAlign. It also creates the necessary
        folders and files for exporting the results.
        """
        # stack seg_stalign of all targets and pad as necessary to create 3 dimensions np.array
        raw_stack = [target.seg_stalign for slide in self.slides for target in slide.targets]
        shapes = np.array([seg.shape for seg in raw_stack])
        max_dims = [shapes[:,0].max(), shapes[:,1].max()]
        paddings = max_dims-shapes
        stack = np.array([np.pad(r, ((p[0],0),(0,p[1]))) for p,r in zip(paddings, raw_stack)])
        stack = np.transpose(np.flip(stack, axis=(0,1)), (-1,0,1))
        nifti = nib.Nifti1Image(stack, np.eye(4)) # create nifti obj
        nib.save(nifti, os.path.join("VisuAlign-v0_9//custom_atlas.cutlas//labels.nii.gz"))

        visualign_export_folder = os.path.join(self.project.folder,'EXPORT_VISUALIGN_HERE')
        if not os.path.exists(visualign_export_folder):
            os.mkdir(visualign_export_folder)

        with open(os.path.join(self.project.folder,'CLICK_ME.json'),'w') as f:
            f.write('{')
            f.write('"name":"", ')
            f.write('"target":"custom_atlas.cutlas", ')
            f.write('"aligner": "prerelease_1.0.0", ')
            f.write('"slices": [')
            i=0
            for sn,slide in enumerate(self.slides):
                for ti,t in enumerate(slide.targets):
                    filename = get_filename(sn, ti)+'.png'
                    f.write('{')
                    h = raw_stack[i].shape[0]
                    w = raw_stack[i].shape[1]
                    f.write(f'"filename": "{filename}", ')
                    f.write(f'"anchoring": [0, {len(raw_stack)-i-1}, {h}, {w}, 0, 0, 0, 0, -{h}], ')
                    f.write(f'"height": {h}, "width": {w}, ')
                    f.write('"nr": 1, "markers": []}')
                    if i < len(raw_stack)-1: f.write(',')
                    i += 1
            f.write(']}')
        
        super().activate()

    def deactivate(self):
        """
        Deactivate the VisuAlignRunner page. This method
        deletes the JSON file for interfacing with VisuAlign
        along with the segmentation stack. 
        """
        os.remove(os.path.join(self.project.folder,'CLICK_ME.json'))
        os.remove('VisuAlign-v0_9/custom_atlas.cutlas/labels.nii.gz')
        super().deactivate()

    def create_widgets(self):
        """
        Create the widgets for this page. This includes:
        - Run Button: A button to open VisuAlign and start the alignment process.
        - Instructions Label: A label with instructions for the user to follow
        """
        self.run_btn = ttk.Button(
            master=self,
            text="Open VisuAlign",
            command=self.run
        )

        self.instructions_label = ttk.Label(
            master=self,
            text="Instructions:\n1. Click \"Open VisuAlign\" button\n2. Click File > Open > \"CLICK_ME.json\"\n3. Adjust alignment with VisuAlign until satisfied\n4. Click File > Export > \"EXPORT_VISUALIGN_HERE\"\n5. Close VisuAlign after notification of successful saving of segmentation"
        )

    def show_widgets(self):
        """
        Show the widgets on the page. This method packs the
        run button and instructions label onto the page."""
        self.instructions_label.pack()
        self.run_btn.pack()

    def run(self):
        """
        Run the VisuAlign application. This method changes the
        current working directory to the VisuAlign directory and
        executes the command to run VisuAlign using the Java executable.
        After VisuAlign has been run, it calls `load_results`
        to load the results from the exported files.
        """
        print("running visualign")
        cmd = rf"cd VisuAlign-v0_9 && {os.path.join("bin","java.exe")} --module qnonlin/visualign.QNonLin"
        os.system(cmd)
        self.load_results()
    
    def load_result_filename(self, filename):
        """
        Load the results from a specified filename. This method checks if the
        exported files from VisuAlign exist, and if so, it processes the results
        to extract the segmentation and outlines. If the files do not exist,
        it raises an exception indicating that the user needs to run VisuAlign first.
        
        Parameters
        ----------
        filename : str
            The filename of the exported results from VisuAlign.

        Returns
        -------
        seg : np.ndarray
            A numpy array representing the segmentation mask of the Target image.
        """
        
        regions_nutil = pd.read_json(r'resources/Rainbow 2017.json')
        with open(filename, 'rb') as fp:
            buffer = fp.read()
        shape = np.frombuffer(buffer, dtype=np.dtype('>i4'), offset=1, count=2) 
        data = np.frombuffer(buffer, dtype=np.dtype('>i2'), offset=9)
        
        data = data.reshape(shape[::-1])
        data = data[:-1,:-1]
        
        names = regions_nutil['name'].to_numpy()[data] 
        seg = names.copy()
        for region_name in np.unique(names):
            mask = names==region_name
            seg[mask] = self.atlases['names'].id[region_name]
        
        return seg.astype(int)

    def load_results(self):
        """
        Load the results from VisuAlign. This method processes
        the results to extract the segmentation and outlines and
        saves them.
        """
        
        for sn,slide in enumerate(self.slides):
            for ti,t in enumerate(slide.targets):
                visualign_nl_flat_filename = os.path.join(self.project.folder,
                                                          "EXPORT_VISUALIGN_HERE",
                                                          get_filename(sn,ti)+"_nl.flat")
                
                try:
                    print(f'we are looking for {visualign_nl_flat_filename}')
                    t.seg_visualign = self.load_result_filename(visualign_nl_flat_filename)
                except:
                    # if not found, use stalign segmentation instead
                    print(f"visualign manual alignment not performed for slice #{sn}, target #{ti}, using stalign semiautomatic alignment")
                    t.seg_visualign = t.seg_stalign.copy()

                # save segmentation
                self.save_results(sn, ti)

    def save_results(self, slideIndex, targetIndex):
        """
        Save the results from VisuAlign for a specific slide and target.
        This method processes the results to extract the segmentation and
        outlines, and saves them in the respective target folder.

        Parameters
        ----------
        slideIndex : int
            The index of the slide for which to save the results.
        targetIndex : int
            The index of the target for which to save the results.
        """
        folder_path = os.path.join(
            self.project.folder, 
            get_folder(
                slideIndex, 
                targetIndex, 
                self.project.stalign_iterations
            )
        )
        target = self.slides[slideIndex].targets[targetIndex]

        # save segmentation
        np.save(
            os.path.join(
                folder_path,
                "visualign_segmentation.npy"
            ),
            target.seg_visualign
        )

        # save outlines
        outlines = (255*target.get_img(seg="visualign")).astype(np.uint8)
        ski.io.imsave(
            os.path.join(
                folder_path,
                "visualign_outlines.png"
            ),
            outlines
        )
        print(f"saved visualign results for slide #{slideIndex}, target #{targetIndex}")

    def done(self):
        """
        Finalize the VisuAlignRunner page's actions. This method
        processes the results from VisuAlign, extracting the segmentation
        and outlines from the exported files. It saves the segmentation
        and outlines in the respective target folders, and updates the
        target's segmentation attribute with the visualign segmentation.
        """
        #TODO: handle if visualign adjustment not used (no exported files)
        self.load_results()

        super().done()
    
    def cancel(self):
        """
        Cancel the actions on the VisuAlignRunner page. This method
        clears the VisuAlign segmentation for each target, effectively
        resetting the manual alignment results.
        """
        for slide in self.slides:
            for target in slide.targets:
                target.seg_visualign = None
        super().cancel()

class RegionPicker(Page):
    """
    Page for selecting regions of interest (ROIs) from the atlas.
    This page allows the user to select regions from a tree view
    of the atlas regions and visualize the selected regions on
    the target images.
    """

    def __init__(self, master, project):
        super().__init__(master, project)
        self.header = "Selecting ROIs"
        self.currSlide = None
        self.currTarget = None
        self.rois = []
        self.region_colors = ['red','yellow','green','orange','brown','white','black','grey','cyan','pink','tan']
    
    def activate(self):
        """
        Activate the RegionPicker page. This method initializes the
        region tree view with the atlas regions, sets up the slide and
        target navigation comboboxes, and ensures the widgets are displayed.
        It also calls `make_tree` to populate the region tree with the
        atlas regions if it hasn't been done yet.
        """
        self.slide_nav_combo.config(
            values=[i+1 for i in range(len(self.slides))]
        )

        if len(self.region_tree.get_children()) == 0:
            self.make_tree()

        super().activate()
    
    def deactivate(self):
        """
        Deactivate the RegionPicker page. This method calls
        the parent class's deactivate method to finalize
        the page's actions.
        """
        super().deactivate()

    def make_tree(self):
        """
        Create the region tree view with the atlas regions. This method
        populates the region tree with the regions from the atlas,
        setting the region names as the text and the region IDs as the
        item IDs. It also sets the parent structure ID for each region
        to create a hierarchical structure in the tree view.
        """
        regions = self.atlases['names']
        for name,row in regions.iterrows():
            id = row['id']
            parent = row['parent_structure_id']
            if pd.isna(parent): parent = ""
            self.region_tree.insert(
                parent=parent,
                index="end",
                iid=id,
                text=name
            )
        self.region_tree.expand_all()

    def create_widgets(self):
        """
        Create the widgets for this page. This includes:
        - Menu Frame: Contains navigation controls for slides and targets.
        - Slice Frame: Contains the figure to display the target image
        with the selected regions overlaid.
        - Region Frame: Contains the tree view for selecting regions
        of interest (ROIs).
        """
        self.menu_frame = tk.Frame(self)
        self.slice_frame = tk.Frame(self)
        self.region_frame = tk.Frame(self)

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
        self.target_nav_combo.bind('<<ComboboxSelected>>', self.update)

        self.slice_viewer = TkFigure(self.slice_frame, toolbar=True)
        self.slice_viewer.canvas.mpl_connect('motion_notify_event', self.on_move)
        self.slice_viewer.canvas.mpl_connect('button_press_event', self.on_click)

        self.region_tree = self.ModifiedCheckboxTreeView(
            master=self.region_frame
        )

        self.region_tree.bind('<Motion>',self.check_update)
        self.region_tree.bind('<ButtonRelease-1>',self.check_update)

    def show_widgets(self):
        """
        Show the widgets on the page. This method packs the
        menu frame, slice frame, and region frame onto the page,
        configures the grid layout, and sets up the navigation
        controls for slides and targets. It also updates the slice
        viewer to display the current target image with the selected
        regions overlaid.
        """
        self.update()
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=1)

        self.menu_frame.grid(row=0, column=0, sticky='nsew')
        self.slice_frame.grid(row=1, column=0, sticky='nsew')
        self.region_frame.grid(row=0, rowspan=2, column=1, sticky='nsew')

        self.slide_nav_label.pack(side=tk.LEFT)
        self.slide_nav_combo.pack(side=tk.LEFT)
        
        self.target_nav_combo.pack(side=tk.RIGHT)
        self.target_nav_label.pack(side=tk.RIGHT)

        self.slice_viewer.get_widget().pack(expand=True, fill=tk.BOTH)

        self.region_tree.pack(expand=True, fill=tk.BOTH)
        #TODO: figure out how to make entire tree horizontal visible

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
        self.update()

    def check_update(self, event=None):
        """
        Check if the selected regions have changed and update the
        segmentation display accordingly. This method retrieves the
        currently checked regions from the region tree, compares them
        with the previously selected regions, and updates the segmentation
        display if there are any changes.
        """
        new_rois = [int(float(s)) for s in self.region_tree.get_checked_no_children()]
        if self.rois != new_rois:
            self.rois = new_rois
            self.show_seg()

    def update(self, event=None):
        """
        Update the figure displaying the segmentation for the current target.
        This method retrieves the current slide and target indices, ensures
        the dropdowns are correctly configured, and displays the segmentation
        for the current target with the selected regions overlaid.
        
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
        self.rois = [int(float(s)) for s in self.region_tree.get_checked_no_children()]
        self.show_seg()

    def show_seg(self):
        """
        Show the current target with the selected regions overlaid.
        This method clears the current axes in the slice viewer, retrieves
        the segmentation image for the current target, and overlays the
        selected regions on the segmentation image. It uses the region colors
        to visualize the selected regions, creating a mask for each checked
        region and displaying them on the segmentation image.
        """
        self.slice_viewer.axes[0].cla()
        seg_img = self.currTarget.get_img(seg="visualign")
        seg = self.currTarget.seg_visualign
        data_regions = np.zeros_like(seg)

        # create masks for each checked region
        for roi in self.rois:
            mask = self.make_region_mask(self.currTarget, roi) * (roi)
            data_regions += mask
        
        self.slice_viewer.axes[0].imshow(ski.color.label2rgb(
            data_regions,
            seg_img, 
            bg_label=0,
            bg_color=None,
            saturation=1,
            alpha=.7,
            image_alpha=1,
            colors=self.region_colors
        ))
        self.slice_viewer.update()
            
    def make_region_mask(self, target, id):
        """
        Create a mask for the specified region ID and its children. This 
        method generates a binary mask where the pixels corresponding to 
        the specified region ID and the region IDs of its children are 
        set to 1, and all other pixels are set to 0.

        Parameters
        ----------
        target : Target
            The target for which the mask is created.
        id : int
            The ID of the region for which the mask is created.
        
        Returns
        -------
        mask : ndarray
            A binary mask with the same shape as the segmentation image,
            where pixels belonging to the specified region and its children 
            are set to 1.
        """
        seg = target.seg_visualign
        mask = (seg==id).astype(int)
        for child in self.region_tree.get_children(str(float(id))):
            mask += self.make_region_mask(target, int(float(child)))
        return mask

    def on_move(self, event):
        """
        Update the title of the slice viewer with the name of the region
        under the mouse cursor. This method retrieves the pixel coordinates
        from the mouse event, gets the region ID from the segmentation image
        at those coordinates, and updates the title of the slice viewer with
        the name of the region corresponding to that ID. If the mouse is not
        over an axes, it does nothing.
        
        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            The mouse event containing the x and y coordinates of the mouse cursor.
        """
        if event.inaxes:
            x,y = int(event.xdata), int(event.ydata)
            id = self.currTarget.seg_visualign[y,x]
            name = self.get_region_name(id)
            self.slice_viewer.axes[0].set_title(name)
            self.slice_viewer.update()
        
    def on_click(self, event=None):
        """
        Handle mouse click events on the slice viewer. This method checks
        if the mouse click occurred within the axes of the slice viewer, retrieves
        the pixel coordinates from the mouse event, and toggles the checked state
        of the region corresponding to the pixel coordinates in the region tree.
        If the region is already checked, it unchecks it and vice versa. It also
        updates the segmentation display after toggling the checked state.
        
        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent, optional
            The mouse event containing the x and y coordinates of the mouse click.
        """
        if event.inaxes:
            x,y = int(event.xdata), int(event.ydata)
            id = float(self.currTarget.seg_visualign[y,x])
            if self.region_tree.tag_has("checked", id):
                self.region_tree._uncheck_descendant(id)
                self.region_tree._uncheck_ancestor(id)
            else:
                self.region_tree._check_ancestor(id)
                self.region_tree._check_descendant(id)
            self.update()
            
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
    
    def get_region_name(self, id):
        """
        Get the name of the region corresponding to the specified ID.
        This method retrieves the region DataFrame from the atlases dictionary,
        locates the row with the specified ID, and returns the index (name) of that
        region.

        Parameters
        ----------
        id : int
            The ID of the region for which to get the name.
        
        Returns
        -------
        name : str
            The name of the region corresponding to the specified ID.
        """
        region_df = self.atlases['names']
        return region_df.loc[region_df.id==id].index[0]

    def cancel(self):
        """
        Cancel the actions on the RegionPicker page. This method calls
        the parent class's cancel method to finalize the page's actions.
        """
        super().cancel()

    def done(self):
        """
        Finalize the RegionPicker page's actions. This method processes
        the selected regions and saves them in a JSON file. Then, this method
        splits each region into clusters using DBSCAN, creates concave hulls
        for each cluster, and saves the boundaries of these hulls in the target's
        `region_boundaries` attribute. It also assigns wells to each region
        based on the row and column indices, ensuring that wells are spread apart
        """

        with open(os.path.join(self.project.folder, 'regions.json'), 'w') as f:
            json.dump(self.rois, f)

        well = lambda r,c: f'{chr( ord('A') +r )}{c+1}'
        spread = 2 # how far wells should be spread apart
        for slide in self.slides:
            row = 0
            col = 0
            for target in slide.targets:
                for roi in self.rois:
                    roi_name = self.get_region_name(roi)
                    pts = np.argwhere(self.make_region_mask(target, roi))
                    if pts.shape[0] == 0: continue # skip if no points found
                
                    _,labels = dbscan(pts, eps=2, min_samples=5, metric='manhattan')
                    for l in set(labels):
                        if l == -1: continue # these points dont belong to any clusters
                        cluster = pts[labels==l]
                        shape_name = f'{roi_name}_{l}'

                        hull = shapely.concave_hull(shapely.MultiPoint(cluster), 0.1) # get hull for cluster
                        
                        # only hulls defined as polygons can actually be cut out, other hulls will not be shown
                        if hull.geom_type == 'Polygon':
                            bound = shapely.get_coordinates(hull)
                            target.region_boundaries[shape_name] = bound
                            
                            # save well
                            if row >= 8: raise Exception(
                                "Too many ROIs selected, please select less ROIs"
                            )
                            target.wells[shape_name] = well(row, col)
                            col += spread
                            if col >= 12:
                                col %= 12
                                row += spread
        super().done()

    class ModifiedCheckboxTreeView(ttkwidgets.CheckboxTreeview):
        """
        A modified version of the CheckboxTreeview that implements custom
        behavior for checking, unchecking, and tristating items. This class
        extends the `ttkwidgets.CheckboxTreeview` class to provide a tree view
        with checkboxes that can be checked, unchecked, and tristated.

        This class overloads the `_box_click` method to implement custom
        behavior for checking, unchecking, and tristating items based on
        the current state of the checkbox.
        
        It also provides methods to get the checked items and their children,
        as well as a method to get the checked items without their children.
        """

        def __init__(self, master=None, **kw):
            super().__init__(master, **kw)

        def get_checked(self):
            """
            Get the checked items and their children. This method returns
            a list of checked items, including their children, ensuring that
            all descendants of a checked item are also included in the result.
            This method overloads the default behavior to include all checked
            items (parents and children) in the result.
            
            Returns
            -------
            checked : list
                A list of checked items including their children."""
            checked = []

            def get_checked_children(item):
                if not self.tag_has("unchecked", item):
                    ch = self.get_children(item)
                    if self.tag_has("checked", item):
                        checked.append(item)
                    if ch:
                        for c in ch:
                            get_checked_children(c)

            ch = self.get_children("")
            for c in ch:
                get_checked_children(c)
            return checked
        
        def get_checked_no_children(self):
            """
            Get the checked items without their children. This method returns
            a list of checked items, ensuring that no child items of a checked
            item are included in the result.
            
            Returns
            -------
            checked : list
                A list of checked items without their children.
            """
            checked = []
            
            def get_highest_checked_children(item):
                if not self.tag_has("unchecked", item):
                    if self.tag_has("checked", item):
                        checked.append(item)
                    else:
                        for c in self.get_children(item):
                            get_highest_checked_children(c)

            ch = self.get_children("")
            for c in ch:
                get_highest_checked_children(c)
            return checked

        def _box_click(self, event):
            """
            Overload:
            If box is unchecked -> check it 
            If box is checked (and has children) -> make it tristate
            If box is tristate -> make it unchecked
            """
            x, y, widget = event.x, event.y, event.widget
            elem = widget.identify("element", x, y)
            if "image" in elem:
                # a box was clicked
                item = self.identify_row(y)
                if self.tag_has("unchecked", item):
                    self._check_ancestor(item)
                    self._check_descendant(item)
                elif self.tag_has("checked", item) and self.get_children(item):
                    self._tristate_parent(item)
                else:
                    self._uncheck_descendant(item)
                    self._uncheck_ancestor(item)

        def _check_ancestor(self, item):
            """
            Overload:
            Check the box of item and change the state of the boxes of item's
            ancestors accordingly. 
            Modification: parent is always tristate even if all children are
            checked
            """
            self.change_state(item, "checked")
            parent = self.parent(item)
            if parent:
                self._tristate_parent(parent)

class Exporter(Page):
    """
    Page for exporting boundaries of targets. This page exports the outlines
    of the targets in each slide to XML files and saves images with the
    boundaries drawn on them. It also provides a toggle button to select
    or deselect all targets for export, and an export button to initiate
    the export process."""

    def __init__(self, master, project):
        super().__init__(master, project)
        self.header = "Exporting Boundaries."
        self.currSlide = None
        self.exported = []

    def activate(self):
        """
        Activate the Exporter page. This method initializes the slide navigation
        combobox with the number of slides, sets up the exported list to track
        the export status of each target, and prepares the folder structure for
        exporting the outlines and images. It also exports the outlines for each
        target in each slide and saves the images with the boundaries drawn on them.
        """
        self.slide_nav_combo.config(
            values=[i+1 for i in range(len(self.slides))]
        )
        self.exported = [[1 for t in slide.targets] for slide in self.slides] # 1 for not exported, 2 for exported, negative for current export group
        
        for si, slide in enumerate(self.slides):
            for ti, target in enumerate(slide.targets):
                folder_path = os.path.join(
                    self.project.folder,
                    get_folder(si, ti, self.project.stalign_iterations)
                )

                # export outlines
                with open(os.path.join(folder_path, 'outlines_ldm.xml'), 'w') as file:
                    self.export_slide(slide, [ti], file)
                
                # save image with outlines
                image_path = os.path.join(folder_path, 'rois.png')
                self.export_boundary_image(target, image_path)

                print(f'Exported outlines for {get_filename(si, ti)}')
                
        super().activate()

    def export_boundary_image(self, target, path):
        """
        Export the boundary image for a target. This method draws the boundaries
        of the target's regions on the original image and saves it as a PNG file.
        
        Parameters
        ----------
        target : Target
            The target for which to export the boundary image.
        path : str
            The path where the boundary image will be saved.
        """
        
        # Convert the image to PIL format
        image_pil = PIL.Image.fromarray(target.img_original)

        # Create a drawing context
        draw = PIL.ImageDraw.Draw(image_pil)

        # Draw each shape's boundary on the image
        for shape in target.region_boundaries.values(): 
            verts = [(x,y) for y,x in shape]
            # Repeat the first point to close the polygon
            verts.append((shape[0][1], shape[0][0]))  
            draw.line(verts, fill='red', width=5)  # Draw closed polygon
        
        # Save the output image
        image_pil.save(path)

    def create_widgets(self):
        """
        Create the widgets for the Exporter page. This includes:
        - Menu Frame: Contains buttons for toggling selection and exporting.
        - Slide Navigation: A combobox for navigating through the slides.
        - Slide Viewer: A figure to display the current slide with the targets.
        """
        # menu
        self.menu_frame = tk.Frame(self)
        self.toggle_all_btn = ttk.Button(
            master=self.menu_frame,
            text='',
            command = self.toggle_select
        )
        self.export_btn = ttk.Button(
            master=self.menu_frame,
            text="Export",
            command=self.export,
            state='disabled'
        )

        self.slide_nav_label = ttk.Label(self.menu_frame, text="Slide: ")
        self.curr_slide_var = tk.IntVar(master=self.menu_frame, value='1')
        self.slide_nav_combo = ttk.Combobox(
            master=self.menu_frame,
            values=[],
            state='readonly',
            textvariable=self.curr_slide_var,
        )
        self.slide_nav_combo.bind('<<ComboboxSelected>>', self.update)

        # slide viewer
        self.slides_frame = tk.Frame(self)
        self.slide_viewer = TkFigure(self.slides_frame, toolbar=True)
        self.slide_viewer.canvas.mpl_connect('button_press_event', self.on_click)

    def show_widgets(self):
        """
        Show the widgets on the Exporter page. This method packs the
        menu frame and slide viewer onto the page, configures the grid layout,
        and sets up the slide navigation combobox. It also calls the update method
        to initialize the current slide and update the buttons and slide viewer.
        """
        
        self.update() # update buttons, slideviewer, stalign params

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # show menu
        self.menu_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')
        self.slide_nav_combo.pack(side=tk.RIGHT)
        self.slide_nav_label.pack(side=tk.RIGHT)

        self.toggle_all_btn.pack(side=tk.LEFT)
        self.export_btn.pack(side=tk.TOP)

        # show slide viewer
        self.slides_frame.grid(row=1, column=0, sticky='nsew')
        self.slide_viewer.get_widget().pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    def update(self, event=None):
        """
        Update the current slide and display the targets on the slide viewer.
        This method retrieves the current slide index from the slide navigation
        combobox, updates the current slide, clears the axes in the slide viewer,
        and shows the new slide image with the targets overlaid. It also updates
        the buttons based on the export status of the targets in the current slide.
        
        Parameters
        ----------
        event : tk.Event, optional
            The event that triggered the update (default is None).
        """
        self.currSlide = self.slides[self.get_index()]
        self.slide_viewer.axes[0].cla() # clear and show new slide image
        self.update_buttons() # update buttons
        self.show_slide()

    def update_buttons(self):
        """
        Update the state of the toggle all and export buttons based on the
        export status of the targets in the current slide. This method checks
        the export status of each target in the current slide and updates the
        toggle all button text and the export button state accordingly. If any
        target is marked for export (export status < 0), the toggle all button
        text is set to "Deselect All" and the export button is enabled. If all
        targets are not marked for export, the toggle all button text is set to
        "Select All" and the export button is disabled.
        """
        self.toggle_all_btn.config(text="Select All")
        self.export_btn.config(state='disabled')
        for export_status in self.exported[self.get_index()]:
            if export_status < 0: 
                self.toggle_all_btn.config(text="Deselect All")
                self.export_btn.config(state='active')
                return
        
    def show_slide(self):
        """
        Show the current slide with the targets overlaid. This method clears
        the axes in the slide viewer, displays the current slide image, and
        adds rectangles for each target in the current slide. The rectangles
        are colored based on their export status.
        """
        # TODO: show the shapes being exported
        self.slide_viewer.axes[0].imshow(self.currSlide.get_img())
        for i,target in enumerate(self.currSlide.targets):
            edgecolor = NEW_COLOR
            if self.exported[self.get_index()][i] < 0: edgecolor = REMOVABLE_COLOR
            elif self.exported[self.get_index()][i] == 2: edgecolor = COMMITTED_COLOR
            self.slide_viewer.axes[0].add_patch(
                mpl.patches.Rectangle(
                    (target.x_offset, target.y_offset),
                    target.img_original.shape[1], 
                    target.img_original.shape[0],
                    edgecolor=edgecolor,
                    facecolor='none', 
                    lw=3
                )
            )
        self.slide_viewer.update()
    
    def on_click(self, event=None):
        """
        Handle mouse click events on the slide viewer. This method checks if
        the mouse click occurred within the axes of the slide viewer, retrieves
        the pixel coordinates from the mouse event, and toggles the export status
        of the target corresponding to the pixel coordinates.
        
        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent, optional
            The mouse event containing the x and y coordinates of the mouse click.
        """
        if event.inaxes is None: return
        x,y = int(event.xdata), int(event.ydata)
        if event.button == 1:
            for i,target in enumerate(self.currSlide.targets):
                if (target.x_offset <= x <= target.x_offset + target.img_original.shape[1] and 
                    target.y_offset <= y <= target.y_offset + target.img_original.shape[0]):
                    self.exported[self.get_index()][i] *= -1
                    self.update()
                    return
                    
    def export(self, event=None):
        """
        Export the outlines of the targets in the current slide to an XML file.
        This method retrieves the current slide index, checks which targets
        are marked for export, and creates an output filename based on the
        slide index and the target indexes. It then creates the output directory
        if it doesn't exist, opens the output file, and calls the `export_slide`
        method to write the slide data to the XML file. After exporting, it updates
        the export status of the targets in the current slide and refreshes the
        display.
        
        Parameters
        ----------
        event : tk.Event, optional
            The event that triggered the export (default is None).
        """

        slide_index = self.get_index()

        tis = [] # list of target indexes to export
        for i in range(self.currSlide.numTargets):
            if self.exported[slide_index][i] < 0:
                self.exported[slide_index][i] = 2
                tis.append(i)  
        
        output_filename = f'slide{slide_index}targets{'_'.join(list(map(str, tis)))}.xml'
        
        os.makedirs(os.path.join(self.project.folder, "output"), exist_ok=True)
        output_path = os.path.join(self.project.folder, "output", output_filename)

        print(f'Exporting to {output_path}')
        with open(output_path,'w') as file:
            self.export_slide(self.currSlide, tis, file)
        
        self.update()
    
    def export_slide(self, slide, targetIndexes, file):
            """
            Export the outlines of the targets in the slide to an XML file.
            This method writes the calibration points, shape count, and shapes
            of the targets in the slide to the XML file. It also writes the
            XML header and the global coordinates.
            
            Parameters
            ----------
            slide : Slide
                The slide containing the targets to export.
            targetIndexes : list of int
                The indexes of the targets to export.
            file : file object
                The file object to write the XML data to.
            """
            # write the xml header
            file.write("<ImageData>\n")
            file.write("<GlobalCoordinates>1</GlobalCoordinates>\n")
            
            # write the calibration points
            for i,pt in enumerate(slide.calibration_points):
                file.write(f"<X_CalibrationPoint_{i+1}>{pt[0]}</X_CalibrationPoint_{i+1}>\n")
                file.write(f"<Y_CalibrationPoint_{i+1}>{pt[1]}</Y_CalibrationPoint_{i+1}>\n")
            
            # write the shape count
            numShapes = 0
            for ti in targetIndexes:
                numShapes += len(slide.targets[ti].region_boundaries)
            file.write(f"<ShapeCount>{numShapes}</ShapeCount>\n")

            # write the shapes
            numShapesExported = 0
            for ti in targetIndexes:
                t = slide.targets[ti]
                self.write_target_shapes(file, t, ti, numShapesExported)
                numShapesExported += len(t.region_boundaries)

            # close the <ImageData> tag
            file.write("</ImageData>")
    
    def write_target_shapes(self, file, target, targetIndex, numShapesExported):
        """
        Write the shapes of the target to the XML file.
        This method writes the shape count, transfer ID, cap ID, and the coordinates
        of the points in the shape to the XML file. It also handles the offset
        for the target's coordinates.
        
        Parameters
        ----------
        file : file object
            The file object to write the XML data to.
        target : Target
            The target containing the shapes to export.
        targetIndex : int
            The index of the target in the slide.
        numShapesExported : int
            The number of shapes already exported in this file.
        """
        for i,(name,shape) in enumerate(target.region_boundaries.items()):
            file.write(f'<Shape_{numShapesExported + i + 1}>\n')
            file.write(f'<PointCount>{len(shape)+1}</PointCount>\n')
            file.write(f'<TransferID>{name}_target{targetIndex}</TransferID>\n')
            file.write(f'<CapID>{target.wells[name]}</CapID>\n')

            for j in range(len(shape)+1):
                file.write(f'<X_{j+1}>{shape[j%len(shape)][1]+target.x_offset}</X_{j+1}>\n')
                file.write(f'<Y_{j+1}>{shape[j%len(shape)][0]+target.y_offset}</Y_{j+1}>\n')
            
            file.write(f'</Shape_{numShapesExported + i + 1}>\n')

    def toggle_select(self, event=None):
        """
        Toggle the selection of all targets in the current slide. This method
        checks the export status of the targets in the current slide and toggles
        their export status. If any target is marked for export (export status < 0),
        it will deselect all targets (set their export status to positive). If
        all targets are not marked for export, it will select all targets (set
        their export status to negative). It also updates the display to reflect
        the changes in export status.
        
        Parameters
        ----------
        event : tk.Event, optional
            The event that triggered the toggle (default is None).
        """
        currSlide_exported = self.exported[self.get_index()]
        has_neg = False # boolean whether currSlide_exported contains a value < 0
        for export_status in currSlide_exported:
            if export_status < 0: 
                has_neg = True
                break
        
        for i in range(len(currSlide_exported)):
            if currSlide_exported[i] < 0 or not has_neg: currSlide_exported[i] *= -1
        self.update()

    def get_index(self):
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

    def done(self):
        """
        Finalize the Exporter page's actions. This method is calls the parent class's
        done method to finalize the page's actions.
        """
        super().done()
    
    def cancel(self):
        """
        Cancel the actions on the Exporter page. This method calls
        the parent class's cancel method to finalize the page's actions.
        """
        super().cancel()
