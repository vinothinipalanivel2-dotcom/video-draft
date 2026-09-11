"""Deterministic subtitle generator producing standard SubRip (.srt) and WebVTT (.vtt) captions."""

from pathlib import Path
from typing import List, Union

from video_draft.schema.scene_plan import SceneBeat, ScenePlan


def _format_srt_timestamp(seconds: float) -> str:
    """Format float seconds into SRT timestamp format: HH:MM:SS,mmm."""
    total_ms = int(round(seconds * 1000.0))
    hours = total_ms // 3600000
    remainder = total_ms % 3600000
    minutes = remainder // 60000
    remainder = remainder % 60000
    secs = remainder // 1000
    millis = remainder % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _format_vtt_timestamp(seconds: float) -> str:
    """Format float seconds into WebVTT timestamp format: HH:MM:SS.mmm."""
    total_ms = int(round(seconds * 1000.0))
    hours = total_ms // 3600000
    remainder = total_ms % 3600000
    minutes = remainder // 60000
    remainder = remainder % 60000
    secs = remainder // 1000
    millis = remainder % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def generate_subtitles_from_plan(
    plan: ScenePlan,
    output_path: Union[Path, str],
    subtitle_format: str = "srt",
) -> Path:
    """Generate subtitle file (.srt or .vtt) aligned with scene plan narration beats.

    Args:
        plan: The validated ScenePlan with timed scenes.
        output_path: Target filepath for the subtitle artifact.
        subtitle_format: "srt" (default) or "vtt".

    Returns:
        Path to the written subtitle file.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    fmt = subtitle_format.lower()

    if fmt == "vtt":
        lines.append("WEBVTT\n")

    cue_index = 1
    for beat in plan.scenes:
        text = (beat.narration_chunk or beat.overlay_text or beat.title or "").strip()
        if not text:
            continue

        start_str = _format_vtt_timestamp(beat.start_sec) if fmt == "vtt" else _format_srt_timestamp(beat.start_sec)
        end_str = _format_vtt_timestamp(beat.end_sec) if fmt == "vtt" else _format_srt_timestamp(beat.end_sec)

        if fmt == "srt":
            lines.append(f"{cue_index}")
            lines.append(f"{start_str} --> {end_str}")
            lines.append(text)
            lines.append("")
        else:
            lines.append(f"{cue_index}")
            lines.append(f"{start_str} --> {end_str}")
            lines.append(text)
            lines.append("")

        cue_index += 1

    out.write_text("\n".join(lines), encoding="utf-8")
    return out
