import numpy as np
import tkinter as tk
from tkinter import ttk
import os

from pages.base import BasePage
from images import Image
from constants import (DSR, FSL, ALPHA, DEFAULT_STALIGN_PARAMS, NEW_COLOR,
                       COMMITTED_COLOR, REMOVABLE_COLOR)
from utils import get_folder, TkFigure

class TargetProcessor(BasePage):
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
            if n > 0: self.currTarget.thetas = np.divide(thetas_avg,n).astype(int)

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
        
        pix_loc = [ALPHA*x for x in atlas.pix_loc[1:]]
        mesh = np.stack(np.meshgrid(
            np.zeros(1),
            pix_loc[0],
            pix_loc[1],
            indexing='ij'),-1)
        
        L,T = target.get_LT()
        mesh_transformed = (L @ mesh[...,None])[...,0] + T
        slice_img = atlas.get_img(mesh_transformed)
        target.img_estim.load_img(slice_img)
    
    def update_seg_estim(self, target):
        """
        Update the estimated segmentation for the target based on the current
        affine transformation parameters. This method retrieves the atlas for the
        current target, applies the affine transformation to the atlas pixel locations,
        and transforms the segmentation using the target's affine transformation
        parameters. It then updates the target's estimated segmentation with the
        transformed segmentation.
        
        Parameters
        ----------
        target : Target
            The target for which to update the estimated segmentation.
        """
        
        atlas = self.atlases[FSL]
        
        mesh = np.stack(np.meshgrid(
            np.zeros(1),
            target.pix_loc[0],
            target.pix_loc[1],
            indexing='ij'),-1)
        
        L,T = target.get_LT()
        mesh_transformed = (L @ mesh[...,None])[...,0] + T
        slice_seg = atlas.get_img(mesh_transformed, mode='nearest')
        
        target.seg['estimated'] = slice_seg.astype(np.uint32)

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
            self.param_vars['iterations'].set('0')

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
        elif num_iterations == 0: self.basic_combo.set(self.basic_options[4])
        else:
            self.basic_combo.set(f"Advanced settings - estimated duration: "
                                  "{3*num_iterations} seconds") 

    def done(self):
        """
        Finalize the TargetProcessor page's actions. This method uses the atlas
        image estimation to estimate the pixel dimensions for each target,
        creates folders for each target, and writes the affine parameters, landmark
        points, and stalign parameters to text files in the respective target folders.
        """
        
        for si, slide in enumerate(self.slides):
            # estimate pixel dimensions
            slide.estimate_pix_dim()
            for ti,target in enumerate(slide.targets):

                # make target folder
                folder = os.path.join(
                    self.project.folder, 
                    get_folder(si, ti, self.project.stalign_iterations)
                )
                os.mkdir(folder)

                # make and save estimated segmentation
                self.update_seg_estim(target)
                target.save_seg(folder, 'estimated')

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
                if "estimated" in target.seg:
                    target.seg.pop('estimated')
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