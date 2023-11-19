import os
from pathlib import Path
from mousechd.utils.tools import download_file, BASE_URI, CACHE_DIR

urls = {
    "thumbnail.png": f"{BASE_URI}/thumbnail.png",
    "busy_mouse.gif": f"{BASE_URI}/busy_mouse.gif",
    "transturbo.npy": f"{BASE_URI}/transturbo.npy"
}

def download_assets():
    savedir = os.path.join(CACHE_DIR, "Napari", "assets")
    for fname, url in urls.items():
        fname = Path(fname)
        download_file(url, fname, cache_dir=savedir)
        