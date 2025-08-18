# User Guide

## Installation

DART is distributed as a pre-compiled Windows binary in a standalone folder that includes all necessary dependencies. To use the software, download and extract the entire folder from the [Google Drive link](https://drive.google.com/drive/folders/1OZ8UNjqNX_7eInwqjmnIVMsgPvRFYCfx?usp=drive_link), then run the `dart.exe` file inside—no installation or separate Python environment is required.

## Getting Started

Prior to using DART, calibration points must be added to the slide. Although natural landmarks on the sample can be used, we recommend creating artificial calibration points that can be reliably located. To do this, use the laser to mark cross-shaped fiducials in the membrane at the top left, top right, and bottom right corners of the slide (**Figure 1**). Then, take an overview image of the whole slide, including fiducial crosses, to use in DART.

<figure>
    <img src=assets/calibration_points.png alt='Cross Fiducial Example'>
    <figcaption>
        <b>Figure 1. Cross Fiducial Example</b>
    </figcaption>
</figure>

## Load the Data

On the DART starter page (**Figure 2**), select an atlas from several options with varying resolutions and imaging workups. Atlases comprise three components: a reference atlas that contains the spatial cell density of the organ of interest, a labels atlas that maps each voxel from the reference atlas to an ID corresponding to a specific region in the tissue, and a table containing information about the regions and their hierarchical structure. In addition to selecting an atlas, select the sample images by clicking “Browse” and selecting the folder containing the images. DART will load each image in the folder as a separate slide and create a subfolder to store results and intermediate files. 

<figure>
    <img src=assets/starter.png alt="Starter Page">
    <figcaption>
        <b>Figure 2. Starter Page</b>
    </figcaption>
</figure>

## Mark Calibration Points and Select Sections

In the slide processing page (**Figure 3**), annotate the calibration points (marked earlier with the LMD) for each slide and delineate individual sections with a rectangle drawing tool. Since multiple sections can be mounted on a single slide, this allows for bulk processing of several sections on each slide. When annotating images in this software, a common color scheme is used. Red annotations have not been saved, green annotations have been saved, and orange annotations have been recently saved and can be removed with a corresponding button at the top of the page. This color scheme is also applied when annotating calibration points, and it continues throughout the software.

<figure>
    <img src=assets/slide_processor.png alt="Slide Processing Page">
    <figcaption>
        <b>Figure 3. Slide Processing Page</b>
    </figcaption>
</figure>

## Prepare for STalign

The Section Processor Page (**Figure 4**) serves three functions: estimation of an affine transformation to map the atlas to the target section, annotation of landmark points, and adjustment of STalign parameters. Use the four sliders to adjust the various rotation angles and translation values of this affine transform. Add landmark points by clicking corresponding landmarks on the target section image and the atlas image, then clicking “Add Point” in the top menu. Tune the parameters of STalign either at a high-level through the dropdown menu or in detail through the text entries. 

<figure>
    <img src=assets/section_processor.png alt="Section Processor Page">
    <figcaption>
        <b>Figure 4. Section Processor Page</b>
    </figcaption>
</figure>

## Run STalign and View Results

In the STalign Runner Page (**Figures 5, 6, 7**), STalign is run on the section images when the “Run” button is clicked. Upon completion of STalign, the results are displayed by overlaying the calculated region boundaries over the section image (**Figure 7**). 

<figure>
    <img src=assets/stalign_running.png alt="STalign Runner Page">
    <figcaption>
        <b>Figure 5. STalign Runner Page</b>
    </figcaption>
</figure>

<figure>
    <img src=assets/stalign_status_graphs.png alt="STalign Progress Monitor">
    <figcaption>
        <b>Figure 6. STalign Progress Monitor</b>
    </figcaption>
</figure>

<figure>
    <img src=assets/stalign_results.png alt=STalign Results Display>
    <figcaption>
        <b>Figure 7. STalign Results Display</b>
    </figcaption>
</figure>

## Adjust Alignment

In the VisuAlign Runner page (**Figure 8**), make manual adjustments to the alignment using VisuAlign (**Figure 9**). This enables greater control over the alignment. Since VisuAlign is a separate software, DART opens it through the command terminal. 

<figure>
    <img src=assets/visualign_runner.png alt="VisuAlign Runner Page">
    <figcaption>
        <b>Figure 8. VisuAlign Runner Page</b>
    </figcaption>
</figure>

<figure>
    <img src=assets/visualign.png alt="VisuAlign">
    <figcaption>
        <b>Figure 9. VisuAlign</b>
    </figcaption>
</figure>

## Select ROIs

In the region selection page (**Figure 10**), select the regions of interest (ROIs). This can be done by either clicking on the ROIs in the image or by navigating to and toggling the checkbox of the region in the tree view. Each has three possible states: unchecked, checked (marked by a check mark), and tristate (marked by a filled box). Unchecked regions will not be exported for dissection. Checked regions and all their child regions will be exported for dissection together. Tristate regions are the parents of checked regions that are not being exported together. This distinction between checked and tristate regions allows broader groups of regions, for example the cerebral cortex, to be easily selected and exported all together as one shape or split into smaller subregions.

<figure>
    <img src=assets/region_picker.png alt="Region Selection Page">
    <figcaption>
        <b>Figure 10. Region Selection Page</b>
    </figcaption>
</figure>

## Export ROI Boundaries

The export page (**Figure 11**) allows the user to select sections for export. All the sections of a slide can be exported together in one batch file for the slide, or individual sections can be exported. This allows the user to group their LMD cutting jobs as desired.

<figure>
    <img src=assets/exporter.png alt="Export Page">
    <figcaption>
        <b>Figure 11. Export Page</b>
    </figcaption>
</figure>

## Import to LMD

Before importing shapes onto the LMD, switch the LMD to the desired objective for cutting. For example, if the user wants to cut their shapes using the 10x objective, then they must first switch to that objective. Then, click File > Import Shapes and select the .xml file containing the shape(s) to be imported. This will trigger a series of prompts to select shapes and calibrate the LMD. Navigate through these prompts until the final prompt, “Use the actual magnification for all imported shapes?”, is reached. Click “Yes”. 

The shapes list should populate with the imported shapes. Select a shape to view it overlaid on the section, and click “Start cut” to initiate the laser dissection process for this shape. Alternatively, all the shapes may be selected and dissected. Note that DART automatically assigns wells to each shape, spaced out with one well in between . These well assignments may be adjusted in the Leica LMD software.