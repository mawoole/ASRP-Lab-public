"""ASRP Scientific Operating System domain-independent foundation.

Purpose:
    Expose package identity for the ASRP-SciOS foundation.
Responsibilities:
    Identify the implementation version and organize stable public modules.
Inputs:
    None.
Outputs:
    Package version metadata.
Dependencies:
    Python standard library only.
Limitations:
    Sprint-004 adds deterministic in-memory ContextSnapshot generation while
    retaining the minimal kernel and immutable domain boundaries; this is not
    a complete scientific operating system or Context Engine runtime.
"""

__version__ = "0.4.0"

__all__ = ["__version__"]
