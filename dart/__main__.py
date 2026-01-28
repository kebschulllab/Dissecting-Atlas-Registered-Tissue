from dart.app import App


def main():
    """
    Console entry point for the DART GUI.

    This mirrors `python -m dart` behavior so the package installs a
    `dart` console script that launches the GUI.
    """
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()