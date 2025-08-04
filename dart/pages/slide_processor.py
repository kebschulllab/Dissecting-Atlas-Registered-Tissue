import matplotlib as mpl
import numpy as np
import os
import skimage as ski
import tkinter as tk
from tkinter import ttk

from pages.base import BasePage
from constants import COMMITTED_COLOR, REMOVABLE_COLOR, NEW_COLOR
from utils import TkFigure, get_filename

class SlideProcessor(BasePage):
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