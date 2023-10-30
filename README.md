# Napari plugin for MouseCHD project

![](mousechd_napari/assets/thumbnail.png)

*Tool for heart segmentation and congenital heart defect detection in mice.*

## Installation
### From Bundle
(1) Install Napari by following this instruction https://napari.org/stable/tutorials/fundamentals/installation.html#install-as-a-bundled-app
(2) Install `mousechd-napari` plugin:
    * Run Napari
    * `Plugins` --> `Install/Uninstall Plugins ...` --> Search for `mousechd_napari` --> Click on `install`.

### From PyPI
```bash
pip install mousechd_napari
```

### From source
```bash
git clone https://github.com/hnguyentt/mousechd-napari
cd mousechd-napari
conda create -n mousechd_napari python=3.7 # create virtualenv
conda activate mousechd_napari
pip install -e . # install
```

## How to use

