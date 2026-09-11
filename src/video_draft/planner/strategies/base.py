"""Base class and common utilities for archetype scene planning strategies."""

import re
from abc import ABC, abstractmethod
from typing import List, Tuple

from video_draft.schema.brief import CreativeBrief
from video_draft.schema.scene_plan import SceneBeat, ScenePlan


def split_script_into_chunks(script: str, target_chunks: int) -> List[str]:
    """
    Deterministically splits script text into target_chunks coherent segments.
    Splits along sentence boundaries (. ! ?) or clause punctuation (, ; -) without losing words.
    """
    clean_script = script.strip()
    if not clean_script:
        return ["" for _ in range(target_chunks)]

    if target_chunks <= 1:
        return [clean_script]

    # Split into sentences
    raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_script) if s.strip()]

    # If fewer sentences than target chunks, split longer sentences on commas or conjunctions
    if len(raw_sentences) < target_chunks:
        expanded: List[str] = []
        for s in raw_sentences:
            parts = [p.strip() for p in re.split(r"(?<=[,;])\s+", s) if p.strip()]
            if len(parts) > 1 and len(expanded) + len(parts) <= target_chunks + 2:
                expanded.extend(parts)
            else:
                expanded.append(s)
        raw_sentences = expanded

    # If still fewer than target chunks, split roughly by words
    if len(raw_sentences) < target_chunks:
        words = clean_script.split()
        chunk_size = max(1, len(words) // target_chunks)
        result = []
        for i in range(target_chunks):
            start_idx = i * chunk_size
            end_idx = (i + 1) * chunk_size if i < target_chunks - 1 else len(words)
            chunk = " ".join(words[start_idx:end_idx])
            result.append(chunk if chunk else "...")
        return result

    # Group sentences into target_chunks
    total_sentences = len(raw_sentences)
    chunks: List[str] = []
    base_chunk_size = total_sentences // target_chunks
    remainder = total_sentences % target_chunks

    current_idx = 0
    for i in range(target_chunks):
        extra = 1 if i < remainder else 0
        take = base_chunk_size + extra
        chunk_sentences = raw_sentences[current_idx : current_idx + take]
        chunks.append(" ".join(chunk_sentences))
        current_idx += take

    return chunks


def allocate_durations(total_duration: float, proportions: List[float]) -> List[float]:
    """
    Allocates total_duration across beats based on proportions.
    Ensures sum(durations) exactly equals total_duration without floating point drift.
    """
    if not proportions:
        return []

    norm_sum = sum(proportions)
    raw_durations = [round((p / norm_sum) * total_duration, 2) for p in proportions]

    # Reconcile rounding discrepancy to the final beat
    diff = round(total_duration - sum(raw_durations), 2)
    raw_durations[-1] = round(raw_durations[-1] + diff, 2)
    return raw_durations


class BaseArchetypeStrategy(ABC):
    """Abstract protocol for archetype-specific scene planning."""

    @property
    @abstractmethod
    def genre(self) -> str:
        """The archetype genre identifier."""
        pass

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Name of the strategy class."""
        pass

    @property
    @abstractmethod
    def pacing_tempo(self) -> str:
        """Archetype pacing tempo."""
        pass

    @property
    @abstractmethod
    def caption_treatment(self) -> str:
        """Archetype caption/subtitle placement."""
        pass

    @property
    @abstractmethod
    def visual_strategy(self) -> str:
        """Archetype visual composition approach."""
        pass

    @abstractmethod
    def plan(self, brief: CreativeBrief, brief_hash: str) -> ScenePlan:
        """Transforms creative brief into an archetype-tailored ScenePlan."""
        pass
