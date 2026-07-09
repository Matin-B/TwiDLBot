import logging
from typing import Union

from ipdb import set_trace  # type: ignore


def debug() -> None:
    """
    Triggers a debugger (ipdb) breakpoint.
    """
    logging.info("Debugging with ipdb.set_trace()")
    set_trace()


def convert_bytes(size: Union[int, float]) -> str:
    """
    Convert a size in bytes to a human-readable string format with appropriate units

    Args:
        size (Union[int, float]): The size in bytes to be converted.

    Returns:
        str: The converted size as a string with appropriate units (bytes, KB, MB, GB, TB).
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return "%3.1f %s" % (size, x)
        size /= 1024.0
    return size
