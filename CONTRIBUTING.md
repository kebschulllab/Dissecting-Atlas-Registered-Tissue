# DART Contribution Guidelines

Thank you for your interest in improving `DART`! We appreciate all contributions, whether it's improving documention or adding new features.

## Types of Contributions

* Bug reports / fixes
* New features
* Documentation improvements
* Unit tests

## How to Contribute
Here's a simple guide to contributing to DART:

### 1. Create an issue
- Check the [pull requests](https://github.com/rk324/Dissecting-Atlas-Registered-Tissue/pulls) and [issues](https://github.com/rk324/Dissecting-Atlas-Registered-Tissue/issues) to see if there are existing discussions/modifications about a similar topic.
- If your proposed change hasn't already been talked about, create a new issue on the [issues](https://github.com/rk324/Dissecting-Atlas-Registered-Tissue/issues) page.


### 2. Set up your development environment
- First, fork the repository
- Then clone the forked repo and set up a conda enviornment by following the instructions [here](README\#cloning-this-repository).


### 3. Make your changes! 
- Create a branch for your changes.
    - Make sure to name it something that concisely summarizes your change
- While making your changes, make sure to follow good documentation and style guidelines
    - The [PEP 8](https://peps.python.org/pep-0008/) style guidlines are a great resource for Python code style.
    - We also follow the [NumPy Docstring](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard) format.
- You should also write unit tests for any new code your write
    - We use `pytest` for testing. You can run tests with

    ```bash
    pytest --disable-warnings
    ```

    - We will not accept pull requests unless all tests pass.

### 4. Submit a pull request.
- Push your changes and open a pull request against the `main` branch of our repository.
- In the pull request, make sure to include
    - what you changed
    - why you made this change
    - links to any related issues/discussions
