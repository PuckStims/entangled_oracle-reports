"""Compatibility surface for the approved HTML-to-PDF workflow contract.

PDF rendering is intentionally a browser-print workflow. This module preserves
the legacy import checked by the rendering-system tests without introducing a
separate PDF engine.
"""

APPROVED_PDF_WORKFLOW = {
    "route": "browser_print",
    "approved_browser": "Chrome",
    "background_graphics_required": True,
    "html_is_source_of_truth": True,
    "workflow_doc": "products/shared/REPORT_PDF_WORKFLOW.md",
}

__all__ = ["APPROVED_PDF_WORKFLOW"]
