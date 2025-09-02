import pytest
import tkinter as tk

@pytest.fixture
def master(scope="session"):
    root = tk.Toplevel()
    yield root
    root.destroy()