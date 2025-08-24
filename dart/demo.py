import tkinter as tk
from tkinter import ttk
import sys
import os
import pickle

from app import Project
from pages import *
from test.load import *

class Demo(tk.Tk):
    """
    A class to run a demo of a specific page in the application.
    This class allows the user to select a page, run the demo,
    and save the state of the project to a checkpoint file.
    """

    def __init__(self):
        super().__init__()

        self.title("DART Demo")
        
        self.create_page_selector()

        self.demo_frame = tk.Frame(self)
        self.demo_widget = None

        # Buttons
        self.start_btn = ttk.Button(
            master=self,
            text='Start Demo',
            command=lambda: self.run(self.page_dict[self.page_name.get()])
        )
        self.start_btn.pack()

    def create_page_selector(self):
        """
        Create a label and combobox to select the demo page.
        """
        self.page_selector = ttk.Frame(self)
        page_selector_label = ttk.Label(
            self.page_selector, 
            text="Select Demo Page:"
        )

        self.page_dict = {
            'Starter': Starter,
            'SlideProcessor': SlideProcessor,
            'TargetProcessor': TargetProcessor,
            'STalignRunner': STalignRunner,
            'SegmentationImporter': SegmentationImporter,
            'VisuAlignRunner': VisuAlignRunner,
            'RegionPicker': RegionPicker,
            'Exporter': Exporter,
        }

        self.page_name = tk.StringVar(value='Starter')
        page_selector_combobox = ttk.Combobox(
            master=self.page_selector,
            values=list(self.page_dict.keys()),
            state='readonly',
            textvariable=self.page_name
        )

        self.page_selector.grid_columnconfigure(0)
        self.page_selector.grid_columnconfigure(1, weight=1)
        page_selector_label.grid(row=0, column=0)
        page_selector_combobox.grid(row=0, column=1, sticky='ew')
        self.page_selector.pack(expand=True, fill=tk.BOTH)

    def run(self, widget_class):
        """
        Run the demo by creating the widget and activating it.
        """

        self.page_selector.pack_forget()
        self.start_btn.pack_forget()

        project = load_project(self.page_name.get())

        self.demo_widget = widget_class(self.demo_frame, project)

        self.demo_frame.pack(expand=True, fill=tk.BOTH)
        self.demo_widget.activate()

if __name__ == "__main__":
    demo = Demo()
    demo.mainloop()