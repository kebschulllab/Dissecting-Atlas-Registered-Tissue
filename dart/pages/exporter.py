import matplotlib as mpl
import os
import PIL.Image
import PIL.ImageDraw
import tkinter as tk
from tkinter import ttk

from pages.base import BasePage
from utils import get_filename, get_folder, TkFigure
from constants import NEW_COLOR, COMMITTED_COLOR, REMOVABLE_COLOR

class Exporter(BasePage):
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
        
        output_filename = f'{get_filename(slide_index, tis)}.xml'
        
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