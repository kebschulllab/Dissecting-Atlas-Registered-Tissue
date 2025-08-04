import tkinter as tk
from tkinter import ttk
import sys
import os
import pickle

from app import Project
from pages import *

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

        # Buttons
        self.start_btn = ttk.Button(
            master=self,
            text='Start Demo',
            command=lambda: self.run(self.page_dict[self.page_name.get()])
        )
        self.start_btn.pack()

        self.checkpoint_btn = ttk.Button(
            master=self,
            text='Finish & Save Checkpoint',
            command = self.save
        )

        self.project = Project()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.path_checkpoints = os.path.join(script_dir, "checkpoints")

        self.demo_widget = None
        self.checkpoint_name = None

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
            'VisuAlignRunner': VisuAlignRunner,
            'RegionPicker': RegionPicker,
            'Exporter': Exporter,
        }

        self.previous_page = {
            'Starter': None,
            'SlideProcessor': 'Starter',
            'TargetProcessor': 'SlideProcessor',
            'STalignRunner': 'TargetProcessor',
            'VisuAlignRunner': 'STalignRunner',
            'RegionPicker': 'VisuAlignRunner',
            'Exporter': 'RegionPicker',
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

        self.checkpoint_name = f"{widget_class.__name__}_checkpoint.pkl"
        # load previous checkpoint
        previous_page = self.previous_page[self.page_name.get()]
        if previous_page:
            previous_checkpoint = f"{self.previous_page[self.page_name.get()]}_checkpoint.pkl"
            self.load(previous_checkpoint)

        self.demo_widget = widget_class(self.demo_frame, self.project)

        self.demo_frame.pack(expand=True, fill=tk.BOTH)
        self.checkpoint_btn.pack()
        self.demo_widget.activate()

    def load(self, checkpoint):
        with open(os.path.join(self.path_checkpoints, checkpoint), 'rb') as f:
            data = pickle.load(f)
            self.project = data

    def save(self):
        self.demo_widget.done()
        data = self.project
        os.makedirs(self.path_checkpoints, exist_ok=True)
        with open(os.path.join(self.path_checkpoints, self.checkpoint_name), 'wb') as f:
            pickle.dump(data, f)
        self.destroy()

if __name__ == "__main__":
    demo = Demo()
    demo.mainloop()