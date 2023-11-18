def load_sample():
    import os
    import tempfile
    import SimpleITK as sitk
    from mousechd.datasets.utils import anyview2LPS
    
    tmp_dir = os.path.join(tempfile.gettempdir(), "MouseCHD")
    os.makedirs(tmp_dir, exist_ok=True)
    
    if not os.path.isfile(os.path.join(tmp_dir, "sample.nii.gz")):
        from urllib import request
        url = 'https://imjoy-s3.pasteur.fr/public/mousechd-napari/sample.nii.gz'
        request.urlretrieve(url, os.path.join(tmp_dir, "sample.nii.gz"))
        
    img = sitk.ReadImage(os.path.join(tmp_dir, "sample.nii.gz"))
    im = sitk.GetArrayFromImage(img)
    
    return [(im,
             {"name": "sample",
              "scale": img.GetSpacing()[::-1]},
             "image")]
        