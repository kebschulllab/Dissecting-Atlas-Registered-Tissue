import tkinter as tk
from tkinter import ttk

from ..images import *
from ..constants import *
from ..utils import *

from abc import ABC, abstractmethod

class BasePage(tk.Frame, ABC):
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