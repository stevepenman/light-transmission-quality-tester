"""Keep all mutable demo state outside the publication files."""

import os
from pathlib import Path


def data_directory():
    """Create the local demo directory, or an explicitly supplied empty sandbox."""
    path = Path(os.environ.get("WTT_DATA_DIR", Path(__file__).parent / ".demo-data"))
    path = path.expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path
