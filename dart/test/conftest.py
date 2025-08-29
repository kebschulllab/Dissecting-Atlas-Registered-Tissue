import pytest
import tkinter as tk

@pytest.fixture
def master(scope="session"):
    root = tk.Tk()
    yield root
    root.destroy()