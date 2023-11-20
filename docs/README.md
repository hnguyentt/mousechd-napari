# How to use MouseCHD Napari plugin

Video tutorial: [Quick start](https://drive.google.com/drive/u/2/folders/1zMkWgJ65AWfg4uVmaDA62EWGhPR1j7Ss)

This plugin is a tool for heart segmentation and detection of congenital heart diseases in mice. You can run this plugin with your local or remote server's resources.

Segmentation step requires GPU to run so if your local machine does not have a GPU, you can do the computation from a GPU-supported remote server. Refer to [server_setup.md](server_setup.md) for more detail.

## Open MouseCHD Plugin
1. Open Napari
2. On the upper-left conner, choose `Plugin` &rarr; `MouseCHD`

## Load data
### Sample data
For quick test, you can you sample data provided by MouseCHD Napari plugin by: `File` &rarr; `Open Sample` &rarr; `microCTscan`

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