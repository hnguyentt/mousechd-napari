def load_sample():
    import os, shutil
    import SimpleITK as sitk  
    
    from mousechd.utils.tools import CACHE_DIR
    from ._utils import tmp_dir
    
    shutil.copy2(os.path.join(CACHE_DIR, "Napari", "assets", "sample.nii.gz"), os.path.join(tmp_dir, "sample.nii.gz"))
        
    img = sitk.ReadImage(os.path.join(CACHE_DIR, "Napari", "assets", "sample.nii.gz"))
    im = sitk.GetArrayFromImage(img)
    
    return [(im,
             {"name": "sample",
              "scale": img.GetSpacing()[::-1]},
             "image")]
        