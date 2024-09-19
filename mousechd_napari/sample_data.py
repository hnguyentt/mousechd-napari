def load_sample():
    import os
    import SimpleITK as sitk  
    
    from mousechd.utils.tools import CACHE_DIR             
        
    img = sitk.ReadImage(os.path.join(CACHE_DIR, "Napari", "assets", "sample.nii.gz"))
    im = sitk.GetArrayFromImage(img)
    
    return [(im,
             {"name": "sample",
              "scale": img.GetSpacing()[::-1]},
             "image")]
        