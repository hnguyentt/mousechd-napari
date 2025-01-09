# Napari plugin for MouseCHD project

![](https://raw.githubusercontent.com/hnguyentt/mousechd-napari/master/assets/demo.gif)

*Tool for heart segmentation and congenital heart defect detection in mice.*

## Installation
### From Bundle
(1) Install Napari by following this instruction https://napari.org/stable/tutorials/fundamentals/installation.html#install-as-a-bundled-app

(2) Install `mousechd-napari` plugin:
    * Run Napari
    * `Plugins` --> `Install/Uninstall Plugins ...` --> Search for `mousechd-napari` --> Click on `install`.

(3) Restart Napari to run the plugin


### Containers
#### Docker

#### Apptainer (Singularity)


### From code
```bash
conda create -n mousechd_napari python=3.9
conda activate mousechd_napari
pip install "napari[all]"
pip install mousechd-napari
napari
```

## How to use
Please find details instruction in folder [docs](https://github.com/hnguyentt/mousechd-napari/tree/master/docs)