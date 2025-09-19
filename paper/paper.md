---
title: 'DART: A GUI Pipeline for Aligning Histological Brain Sections to 3D Atlases and Automating Laser Microdissection'
tags:
  - Python
  - neuroscience
  - laser dissection
  - atlas
  - GUI
authors:
  - name: Rishi Koneru
    affiliation: '1'
    equal-contrib: true
    orcid: 0009-0002-3714-0122
  - name: Manjari Anant
    corresponding: true
    affiliation: '2,3,4'
    equal-contrib: true
    orcid: 0000-0002-6600-3410
  - name: Hyopil Kim
    affiliation: '1'
    orcid: 0000-0001-9159-8682
  - name: Julian Cheron
    affiliation: '1'
    orcid: 0000-0001-6369-0019
  - name: Justus M. Kebschull
    corresponding: true
    affiliation: '1,2,3,5'
    orcid: 0000-0002-4851-0267
affiliations:
  - index: 1
    name: Department of Biomedical Engineering, Johns Hopkins University, Baltimore, MD 21205, USA
  - index: 2
    name: Department of Neuroscience, Johns Hopkins University, Baltimore, MD 21205, USA
  - index: 3
    name: Kavli Neuroscience Discovery Institute, Johns Hopkins University, Baltimore, MD 21205, USA
  - index: 4
    name: Center for Computational Biology, Johns Hopkins University, Baltimore, MD 21205, USA
  - index: 5
    name: Center for Functional Anatomy and Evolution, Johns Hopkins University, Baltimore, MD 21205, USA
date: 25 August 2025
bibliography: paper.bib
---

# Summary

The precise dissection of anatomically defined brain regions is the basis of many workflows in neurobiology. Traditionally, brain regions of interest are defined by visual inspection of tissue sections, followed by manual dissection. Recently, laser capture microscopes have been employed for more accurate dissection, but region identification remains challenging. This paper presents an open-source software pipeline [D]{.ul}issecting [A]{.ul}tlas-[R]{.ul}egistered [T]{.ul}issue (DART) that aligns histological brain sections to three-dimensional reference atlases and exports the resulting region-of-interest (ROI) contours for dissection by Leica Laser Microdissection (LMD) instruments. By integrating well-established image-processing libraries with a user-friendly graphical user interface, the software automates the traditionally time-consuming workflow of defining the boundaries of brain regions for dissection. With this pipeline, researchers can streamline tissue sampling for molecular analyses, while ensuring reproducibility and precision in ROI selection.

# Statement of Need

There is a growing demand for precise, automated methods to identify and dissect regions of interest (ROIs) in histological brain sections. The brain is highly heterogeneous, with distinct molecular and connectomic profiles across regions, making accurate region dissection critical for biological interpretation. For example, proteomic analyses, bulk RNA sequencing, and connectomic techniques like MAPseq often require the precise dissection of dozens to hundreds of brain regions [@Webb2015; @Goto-Silva2021; @Huang2020; @Kim2025; @Kebschull2016; @Chen2019]​. Laser microdissection (LMD) enables highly accurate dissection of biological tissues; however, current approaches using LMD require manual delineation of brain regions, which is error-prone and time consuming. Moreover, the lack of a standardized region selection makes it difficult to ensure consistent, reproducible sampling across experiments and laboratories. Existing open-source tools enable atlas alignment and segmentation of histological brain section images (e.g. STalign, QuickNII, and VisuAlign) [@Clifton2023; @Puchades2019]​. However, no tools currently integrate atlas alignment and region selection with Leica LMD software to enable seamless and precise dissection of those regions.

The Dissecting Atlas Registered Tissue (DART) pipeline (\autoref{fig1}) addresses this gap by providing:

1. Automated or semi-automated alignment of 2D brain sections to a 3D reference brain atlas and atlas-based segmentation.
2. Seamless integration with Leica LMD software for laser dissection.
3. Clear documentation and an accessible, modular codebase, facilitating further development and customization by the community.

# Software Overview

## Key Features

1. **Atlas Alignment:** Combination of STalign [@Clifton2023]​ for landmark-based semi-automatic registration and Visualign [@Puchades2019]​ for manual registration to a 3D reference brain atlas generates affine and non-linear transformations to map 2D section coordinates onto known brain regions.
2. **GUI Control:** A GUI for real-time quality control and manual correction of section alignment.
3. **Extensibility:** Open-source architecture allowing integration of new or customized registration algorithms, region-detection heuristics, and atlases.
4. **High-throughput Multi-Sample Processing:** Slide segmentation tools allow users to upload images of whole slides with multiple sections and export the ROI outlines.
5. **ROI Selection:** User-guided selection of atlas-defined regions in aligned sections.
6. **Integration with LMD:** Conversion of regions and metadata (e.g. atlas region names) into shape files compatible with Leica LMD with flexibility in ROI dissection magnification.

![**The DART workflow.** The 3D renderings of the Allen atlas were produced using brainrender [@Wang2020; @Claudi2021]​.\label{fig1}](workflow.png)

# Application

To demonstrate its utility, we applied DART to dissect the primary and secondary somatomotor areas and the anterior commissure from a coronal section of an adult mouse brain (\autoref{fig2}). Starting with a Nissl-stained section, we used DART to align the section to a DAPI-based atlas [@Stger2020]​ and generated outlines for the target regions. Importing these outlines into the Leica LMD system enabled precise laser cutting.

![**A DART use case.** A DART application begins with an image of the original section. It then generates a segmentation, selects desired regions, and exports to the LMD for cutting or etching with the laser as desired. Note: Images were restitched using the Stitching plugin in ImageJ [@Preibisch2009]​.\label{fig2}](dissection_results.png)

# Discussion and Limitations

Our open-source workflow simplifies consistent region identification and dissection across multiple brain sections. However, certain limitations remain:

- **Staining Variability:** Significant differences in staining intensity or section thickness can reduce alignment accuracy.
- **Atlas Mismatch:** Anatomical variability between individual subjects and the reference atlas may necessitate manual adjustment, especially in samples from disease models.
- **Tissue Damage:** Significant deformation to sections from holes or tears in the tissue can reduce alignment accuracy.
- **ROI Complexity:** Highly intricate or irregular regions might require manual editing of automatically generated ROIs.

Future improvements of DART may include support for alternative alignment algorithms, expanded atlas selection covering additional species and organ systems, and expanded compatibility with additional microscope systems beyond Leica LMD.

# Conclusions

Here we present an open-source pipeline that aligns histological brain sections to 3D reference atlases and seamlessly exports brain-region defined ROIs for Leica Laser Microdissection. By automating key steps in the tissue sampling process, researchers can reduce manual labor, improve reproducibility, and accelerate downstream molecular assays. The modular, documented codebase invites community contributions and adaptation to new species, atlases, and laboratory workflows.

## Code Availability:

DART is hosted on Github: [https://github.com/rk324/Dissecting-Atlas-Registered-Tissue](https://github.com/rk324/Dissecting-Atlas-Registered-Tissue)

## Data Collection

All mouse procedures were conducted in accordance with the Johns Hopkins University Animal Care and Use Committee (ACUC) protocols MO20M376 and MO23M346. Mice were maintained on a 12-hour light/dark cycle with ad libitum access to food and water. Brain sections for LMD were prepared as previously described​ [@Kim2025_]​.

## Acknowledgments

We would like to thank the open-source community for providing foundational libraries such as VisuAlign, STalign, and Tkinter. This work was supported by SFARI grant 875575 and NIH grants DP1DA056668 and RF1AG078378 to JMK and a Kavli NDI Distinguished predoctoral fellowship to MA.

## Conflicts of interest

The authors declare no conflicts of interest.

# References
