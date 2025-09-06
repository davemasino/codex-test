"""Utilities for working with Informatica PowerCenter workflows."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

__all__ = ["__version__", "count_mappings"]

__version__ = "0.1.0"


def count_mappings(workflow_path: str | Path) -> int:
    """Count ``MAPPING`` elements in a workflow document.

    Parameters
    ----------
    workflow_path:
        Path to an Informatica PowerCenter workflow XML document.

    Returns
    -------
    int
        Number of ``MAPPING`` elements found in the document.
    """

    tree = ET.parse(workflow_path)
    return len(tree.findall(".//MAPPING"))
