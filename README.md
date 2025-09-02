## Overview

Dissecting Atlas-Registered Tissue (DART) aligns cell-stained images to the Allen Brain Atlas to allow for automatic brain region detection and excision with LEICA laser microdissection software. 

DART enables:
- Automated or semi-automated alignment of 2D brain slices to a 3D atlas (e.g., the Allen Brain Atlas CCFv3 2017) and atlas-based segmentation. 
- Automatic generation of ROI boundaries.
- Seamless sample handling and integration with Leica LMD software for laser dissection. 

<figure>
    <img src=DART_alignment_results.png alt="DART Alignment Results">
    <figcaption>
        <>DART alignment results on various brain sections</>
    </figcaption>
</figure>

## Installation

### Executable File (no coding experience required)
DART is distributed as a pre-compiled Windows binary in a standalone folder that includes all necessary dependencies. To use the software, download and extract the entire folder from the [Google Drive link](https://drive.google.com/file/d/1UHvkmNt6kgneh7vLTZS29K53wJkYFOEJ/view?usp=sharing), then run the `main.exe` file inside—no installation or separate Python environment is required.

### OR

### Cloning this repository (Suitable for editing/contributing to the software, Required for testing via pytest)
First, clone this repository using `git clone https://github.com/rk324/Dissecting-Atlas-Registered-Tissue.git`
Next, set up a conda environment by navigating into the repository folder and using `conda env create -f environment.yml`

Finally, download and extract the [atlases folder](https://drive.google.com/file/d/1zSF-S4CuY199EhDk4VU8NO6_jrEVNuMs/view?usp=sharing) and move the result into the repo. 
The `atlases` folder should have 5 subfolders, and each of those should have 3 subfiles titled `label.nrrd`, `reference.nrrd`, and `names_dict.csv`.

## Input Data
To use this tool, you will need provide the following information:

- 3D Reference Atlas with cell stain and region annotations (included in installation if using Allen Brain Atlas)
- A folder containing cell stained images from LEICA LDM on slides 

## Usage

To use `DART`, please refer to our [tutorial](tutorials/README.md).

## License
- DART's source code is available under the GNU General Public License version 3
- VisuAlign is developed by the Neural Systems Laboratory at the Institute of Basic Medical Sciences, University of Oslo, Norway and is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 License](https://creativecommons.org/licenses/by-nc-sa/4.0/)

## Contributing
For support or issues, please open an “Issue” on our GitHub repository. To contribute to the software, please email manjari.anant@gmail.com and rishikoneru2005@gmail.com.


