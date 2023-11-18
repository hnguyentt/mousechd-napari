import os
import re
import tempfile
import pydicom
import numpy as np
import SimpleITK as sitk

from mousechd.datasets.utils import dicom2nii, nrrd2nii, anyview2LPS, make_isotropic

tmp_dir = os.path.join(tempfile.gettempdir(), "MouseCHD")
os.makedirs(tmp_dir, exist_ok=True)

def napari_get_reader(path):
    if isinstance(path, list) and path.endswith((".nii.gz", ".nrrd")):
        path = path[0]
        print(path)
    
    return reader_function


def reader_function(path):
    """Take a path or list of paths and return a list of LayerData tuples.

    Readers are expected to return data as a list of tuples, where each tuple
    is (data, [add_kwargs, [layer_type]]), "add_kwargs" and "layer_type" are
    both optional.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple in the list contains
        (data, metadata, layer_type), where data is a numpy array, metadata is
        a dict of keyword arguments for the corresponding viewer.add_* method
        in napari, and layer_type is a lower-case string naming the type of
        layer. Both "meta", and "layer_type" are optional. napari will
        default to layer_type=="image" if not provided
    """
    
    if os.path.isdir(path):
        first_file = next(os.path.join(path, f) for f in os.listdir(path) if not f.startswith(".") and f.endswith(".dcm"))
        dicom_data = pydicom.read_file(first_file)
        mouse = str(dicom_data.get("PatientName")).replace(" ", "")
        img = dicom2nii(path)
    else:
        if path.endswith(".nii.gz"):
            mouse = re.sub(r".nii.gz$", "", os.path.basename(path))
            img = sitk.ReadImage(path)
        else:
            mouse = re.sub(r".nrrd$", "", os.path.basename(path))
            img = nrrd2nii(path)
    
    mouse = re.sub(r"_0000", "", mouse)
    img = anyview2LPS(img)
    img = make_isotropic(img, spacing=0.02)
    im = sitk.GetArrayFromImage(img)
    sitk.WriteImage(img, os.path.join(tmp_dir, f"{mouse}.nii.gz"))
    
    add_kwargs = {"name": mouse, 
                  "scale": img.GetSpacing()[::-1]}
    
    return [(im, add_kwargs, "image")]
        
        
        