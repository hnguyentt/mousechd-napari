__version__ = "0.0.4"

from ._widget import MouseCHD
from ._reader import napari_get_reader

__all__ = (
    "napari_get_reader",
    "MouseCHD"
)