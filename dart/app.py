import tkinter as tk
from tkinter import ttk
from images import Atlas, Slide
from pages import *
from constants import FSR, DSR, FSL, DSL

class Project():
    """
    Project class to store all data, results, and metadata

    Attributes
    ----------
        slides : list
            List of Slide objects.
        atlases : dict 
            Dictionary containing atlas information.
        parent_folder : str
            String storing path to parent folder containing images
        folder : str
            String storing path to project folder storing intermediate files
        stalign_iterations : int
            Integer tracking number of times stalign has been run
    """
    def __init__(self):
        self.slides: list[Slide] = []
        self.atlases = {
            FSR: Atlas(),
            DSR: Atlas(),
            FSL: Atlas(),
            DSL: Atlas(),
            'names': None
        }
        self.parent_folder = None
        self.folder = None

class App(tk.Tk):
    def __init__(self):
        # initializes app with main window, navigation bar, prev/next buttons in nav_bar, 
        super().__init__()
        self.create_widgets()
        self.show_widgets()

        self.project = Project()

        # initalize each page with self.main_window as parent
        page_list: tuple[BasePage] = tuple([
            Starter, 
            SlideProcessor, 
            TargetProcessor,
            STalignRunner,
            VisuAlignRunner,
            RegionPicker,
            Exporter
        ])
        self.pages: list[BasePage] = [page(self.main_window, self.project) for page in page_list]
        self.page_index = 0
        self.update()

    def create_widgets(self):
        self.main_window = tk.Frame(self)
        self.page_label = ttk.Label(self.main_window)

        self.nav_bar = tk.Frame(self)
        self.prev_btn = ttk.Button(self.nav_bar, command=self.prev_page)
        self.next_btn = ttk.Button(self.nav_bar, command=self.next_page)

    def show_widgets(self):
        # show nav_bar and main_window
        self.main_window.pack(expand=True, fill=tk.BOTH)
        self.page_label.pack()

        self.nav_bar.pack(side=tk.BOTTOM)
        self.prev_btn.pack(side=tk.LEFT)
        self.next_btn.pack(side=tk.RIGHT)
    
    def next_page(self):
        self.pages[self.page_index].done()
        if self.page_index == len(self.pages)-1:
            self.destroy()
            return
        self.page_index += 1
        self.update()

    def prev_page(self):
        self.pages[self.page_index].cancel()
        if self.page_index == 0: 
            self.destroy()
            return
        self.page_index -= 1
        self.update()
    
    def update(self):
        current_page = self.pages[self.page_index]
        
        # activate current page
        current_page.activate()

        # set header label
        self.page_label.config(text=current_page.get_header())

        # logic for showing next and previous buttons
        self.prev_btn.config(text='Previous')
        self.next_btn.config(text='Next')
        if self.page_index == 0:
            self.prev_btn.config(text='Exit')
        
        if self.page_index == len(self.pages)-1:
            self.next_btn.config(text='Finish')
    
    def skip_inbuilt_segmentation(self):
        """
        Modifies the page order to bypass the inbuilt segmentation steps.
        This method is called when the user selects a custom segmentation method
        in the Starter page. It removes the TargetProcessor and STalignRunner pages
        from the navigation flow, allowing the user to proceed directly to the
        VisuAlignRunner page after completing the SlideProcessor page.
        """
        
        # remove TargetProcessor and STalignRunner pages from the navigation flow
        target_processor_page = self.pages.pop(2)
        stalign_runner_page = self.pages.pop(2)
        target_processor_page.destroy()
        stalign_runner_page.destroy()

        # insert SegmentationImporter page after SlideProcessor
        self.pages.insert(2, SegmentationImporter(self.main_window, self.project))