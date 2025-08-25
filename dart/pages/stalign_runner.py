import numpy as np
import os
import pickle
import skimage as ski
from .. import STalign
import tkinter as tk
from tkinter import ttk
import torch

from .base import BasePage
from ..constants import ALPHA, FSR, DSR, FSL 
from ..utils import get_target_name, LDDMM_3D_LBFGS, TkFigure


class STalignRunner(BasePage):
    """
    Page for running STalign and viewing results. This page runs 
    STalign, showing a progress bar, and then displays results once
    completed. It also saves graphs related to STalign runtime and 
    error tracking.
    """

    def __init__(self, master, project):
        super().__init__(master, project)
        self.header = "Running STalign and Viewing Results."
        self.can_finish = False
    
    def activate(self):
        """
        Activate the STalignRunner page. This method calls 
        `estimate_time` to estimate the duration of STalign and
        configure the progress bar and labels accordingly.
        """
        # TODO: if all skipped -> immediately generate segmentations 
        # and call done()
        super().activate()
        total_iterations = 0
        for slide in self.slides:
            for target in slide.targets:
                total_iterations += target.stalign_params['iterations']

        if total_iterations:
            self.estimate_time(total_iterations)
        else:
            self.can_finish = True
            self.info_label.config(
                text="Skipping STalign, displaying segmentation "
                     "estimations from previous step."
            )
            self.start_btn.pack_forget()
            self.show_results()

    def estimate_time(self, iterations):
        """
        Estimate duration of STalign for all targets. This method
        totals up the iterations for all planned STalign runs and
        calculates the duration of STalign my assuming each iteration
        takes 3 seconds. It also configures the progress bar and 
        text label with this information.

        Parameters
        ----------
        iterations : int
            The total number of iterations of STalign across all
            targets.
        """

        time_sec = 3*iterations # ~3 sec/iteration
        time_str = STalignRunner.seconds_to_string(time_sec)
        label_txt = f'Estimated Duration: {time_str}'
        self.info_label.config(text=label_txt)
        self.progress_bar.config(maximum=iterations)

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
        - Run Button: Allows user to begin running STalign by clicking the
        Run button.
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
            pointsI=processed_points["atlas"],
            pointsJ=processed_points["target"],
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
        )[0,0].cpu().numpy().astype(np.uint32)
        
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
                if target.stalign_params['iterations'] == 0:
                    print(f'Skipping STalign for Slide {sn+1}, Target {tn+1}')
                    continue
                label_txt = f'Running STalign on Slide #{sn+1}, Target #{tn+1}'
                print(label_txt)
                self.info_label.config(text=label_txt)
                self.update()
                figure.clear()
                
                target.transform, errors = self.get_transform(
                    target, 
                    device, 
                    figure
                )
                target.seg['stalign'] = self.get_segmentation(target)

                # saving results
                folder_path = os.path.join(
                    self.project.folder, 
                    get_target_name(sn, tn)
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
                folder = get_target_name(sn, tn)
                target.save_seg(folder_path, 'stalign')

        self.can_finish = True
        stalign_window.destroy()
        self.info_label.config(text="Done!")
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

        if not self.can_finish:
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
                if 'stalign' in target.seg:
                    target.seg.pop('stalign')
        super().cancel()