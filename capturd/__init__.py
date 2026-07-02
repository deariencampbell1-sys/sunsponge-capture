"""Captur'd by Sun Sponge — post-work product capture (stills + walkthrough)."""

__version__ = "0.2.0"

# Stills mode — batch rested-state screenshots
from .shots import (
    RestedCaptureError,
    RestedCaptureManager,
    build_capture_plan,
)

__all__ = [
    "RestedCaptureError",
    "RestedCaptureManager",
    "build_capture_plan",
    "__version__",
]
