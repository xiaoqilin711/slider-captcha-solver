"""slider-captcha-solver: a research toolkit for slider CAPTCHA automation.

The package is deliberately site-agnostic. Site-specific constants (domains,
CSS selectors, OCR credentials, calibrated offsets, recorded trajectories)
live in the ``examples/`` profiles, never inside the library itself.
"""

__version__ = "0.1.0"

from .track import scale_to_distance, analyze_trace  # noqa: F401

__all__ = ["scale_to_distance", "analyze_trace", "__version__"]
