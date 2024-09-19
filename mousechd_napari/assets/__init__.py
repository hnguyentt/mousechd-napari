import os
from mousechd.utils.tools import download_zenodo, CACHE_DIR


def download_assets():
    savedir = os.path.join(CACHE_DIR, "Napari")
    if not os.path.isfile(os.path.join(savedir, "assets", "sample.nii.gz")):
        download_zenodo(zenodo_id="13785938", filename="assets.zip", outdir=savedir, extract=True)
    
        