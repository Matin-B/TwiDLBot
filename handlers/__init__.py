from .error import router as error_router
from .start import router as start_router
from .downloader import handle_massive_document as downloader_router

__all__ = [
    "error_router",
    "start_router",
    "downloader_router",
]
