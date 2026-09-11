"""Test that all modules and submodules in video_draft import properly."""

import importlib
import pytest


def test_package_import():
    """Verify top-level package can be imported and exposes version."""
    import video_draft
    assert hasattr(video_draft, "__version__")
    assert video_draft.__version__ == "0.1.0"


@pytest.mark.parametrize(
    "submodule",
    [
        "video_draft.cli",
        "video_draft.config",
        "video_draft.schema",
        "video_draft.schema.config",
        "video_draft.schema.brief",
        "video_draft.schema.timeline",
        "video_draft.schema.routing",
        "video_draft.schema.manifest",
        "video_draft.utils",
        "video_draft.utils.logger",
        "video_draft.utils.system_info",
        "video_draft.planner",
        "video_draft.router",
        "video_draft.adapters",
        "video_draft.assembly",
        "video_draft.audio",
        "video_draft.cache",
        "video_draft.evaluation",
    ],
)
def test_submodules_import(submodule: str):
    """Verify all architectural modules and stubs can be imported without error."""
    mod = importlib.import_module(submodule)
    assert mod is not None
