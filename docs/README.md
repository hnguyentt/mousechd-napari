# How to use MouseCHD Napari plugin

Tutorial video: [Quick start](https://drive.google.com/file/d/1nQBw5jj3VtRH8pFlDuih_lmWLfwtr69M/view?usp=sharing)

This plugin serves as a tool for heart segmentation and the detection of congenital heart disorders in mice. You can execute the plugin utilizing the resources of either your local machine or a remote server.

The segmentation step necessitates GPU acceleration. If your local machine lacks a GPU, consider offloading the computation to a remote server with GPU support. Refer to [server_setup.md](server_setup.md) for more detail.

## Open MouseCHD Plugin
1. Open Napari
2. On the upper-left conner, choose `Plugin` &rarr; `MouseCHD`

## Load data
### Sample data
For quick test, you can use sample data provided by MouseCHD Napari plugin: `File` &rarr; `Open Sample` &rarr; `microCTscan`

### Load your own data
* Drag and drop your data on the image display area. Supported format: DICOM folder, NRRD, NIFTI.
* Choose `MouseCHD` as the reader
![](../assets/choose_reader.png)


## Diagnose
1. Choose a resource to run on. If you choose server, please setup your local machine and remote server, following [this instruction](server_setup.md).
2. Choose scan to predict
3. Click on `Diagnose` button

## View GradCAM
TBD

## Retrain
TBD

## Diagnose with retrained model
TBD