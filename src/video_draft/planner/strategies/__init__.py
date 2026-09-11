"""Strategy registry and factory for archetype scene planning."""

from typing import Dict, List

from video_draft.planner.errors import UnsupportedArchetypeError
from video_draft.planner.strategies.base import BaseArchetypeStrategy
from video_draft.planner.strategies.education import EducationStrategy
from video_draft.planner.strategies.news import NewsStrategy
from video_draft.planner.strategies.product import ProductStrategy


_STRATEGY_REGISTRY: Dict[str, BaseArchetypeStrategy] = {
    "education": EducationStrategy(),
    "news": NewsStrategy(),
    "product": ProductStrategy(),
}


def get_strategy(genre: str) -> BaseArchetypeStrategy:
    """
    Retrieves the planning strategy instance for the given genre.
    Raises UnsupportedArchetypeError if the genre is not registered.
    """
    clean_genre = genre.strip().lower() if genre else ""
    if clean_genre not in _STRATEGY_REGISTRY:
        supported = sorted(_STRATEGY_REGISTRY.keys())
        raise UnsupportedArchetypeError(
            f"Unsupported archetype '{genre}'. Must be one of {supported}."
        )
    return _STRATEGY_REGISTRY[clean_genre]


def register_strategy(genre: str, strategy: BaseArchetypeStrategy) -> None:
    """Registers a new archetype strategy into the registry."""
    clean_genre = genre.strip().lower()
    _STRATEGY_REGISTRY[clean_genre] = strategy


def list_supported_archetypes() -> List[str]:
    """Returns a sorted list of all supported archetype genres."""
    return sorted(_STRATEGY_REGISTRY.keys())


__all__ = [
    "BaseArchetypeStrategy",
    "EducationStrategy",
    "NewsStrategy",
    "ProductStrategy",
    "get_strategy",
    "register_strategy",
    "list_supported_archetypes",
]
