<img src="">

`DART` aligns cell-stained images to the Allen Brain Atlas to allow for automatic brain region detection and excision with LEICA laser microdissection software. 

More information regarding the overall approach, methods and validations can be found in our publication:
<a href="">
<b>DART: Dissecting Atlas-Registered Tissue </b>
Rishi Koneru, Manjari Anant^
</a>

## Overview

DART enables:
- Automated or semi-automated alignment of 2D brain slices to a 3D atlas (e.g., the Allen Brain Atlas CCFv3 2017) and atlas-based segmentation. 
- Automatic generation of ROI boundaries.
- Seamless sample handling and integration with Leica LMD software for laser dissection. 

<figure>
    <img src=DART_alignment_results.png alt="DART Alignment Results">
    <figcaption>
        <b>DART alignment results on various brain sections</b>
    </figcaption>
</figure>

## Installation

DART is distributed as a pre-compiled Windows binary in a standalone folder that includes all necessary dependencies. To use the software, download and extract the entire folder from the [Google Drive link](https://drive.google.com/drive/folders/1OZ8UNjqNX_7eInwqjmnIVMsgPvRFYCfx?usp=drive_link), then run the `dart.exe` file inside—no installation or separate Python environment is required.

## Input Data
To use this tool, you will need provide the following information:

- 3D Reference Atlas with cell stain and region annotations(not needed if using Allen Brain Atlas)
- Cell stained images from LEICA LDM on slides 

## Usage

To use `DART`, please refer to our [tutorial](https://docs.google.com/document/d/1vvepQjYQtZjw-hnTglz25f71RQvsMKiJ/edit?usp=sharing&ouid=112930046003306259781&rtpof=true&sd=true).

## License
- DART's source code is available under the GNU General Public License version 3
- VisuAlign is developed by the Neural Systems Laboratory at the Institute of Basic Medical Sciences, University of Oslo, Norway and is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 License](https://creativecommons.org/licenses/by-nc-sa/4.0/)

