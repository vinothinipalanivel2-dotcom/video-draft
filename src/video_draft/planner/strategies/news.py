"""News / Commentary archetype scene planning strategy."""

from datetime import datetime, timezone
from typing import List

from video_draft.planner.strategies.base import BaseArchetypeStrategy, allocate_durations, split_script_into_chunks
from video_draft.schema.brief import CreativeBrief
from video_draft.schema.scene_plan import SceneBeat, ScenePlan


class NewsStrategy(BaseArchetypeStrategy):
    """
    News / Commentary archetype planning strategy.
    Prioritizes fast journalistic pacing, rapid scene cuts, urgent headline framing,
    and bottom-ticker caption metadata.
    """

    @property
    def genre(self) -> str:
        return "news"

    @property
    def strategy_name(self) -> str:
        return "NewsStrategy"

    @property
    def pacing_tempo(self) -> str:
        return "fast_urgent"

    @property
    def caption_treatment(self) -> str:
        return "urgent_bottom_ticker"

    @property
    def visual_strategy(self) -> str:
        return "b_roll_and_broadcast"

    def plan(self, brief: CreativeBrief, brief_hash: str) -> ScenePlan:
        # Journalistic 5-beat rapid structure: Breaking Hook -> Facts -> Detail -> Context -> Wrap
        beat_definitions = [
            {
                "beat_type": "breaking_headline",
                "title": "Breaking Headline Hook",
                "proportion": 0.18,
                "camera_motion": "rapid_push_in",
                "transition_in": "cut",
                "transition_out": "cut",
                "prompt_modifier": "breaking broadcast newsroom, dynamic chyron graphic aesthetic, urgent report framing",
                "ticker": "BREAKING NEWS",
            },
            {
                "beat_type": "core_facts",
                "title": "Primary Event & Facts",
                "proportion": 0.22,
                "camera_motion": "handheld_dynamic_pan",
                "transition_in": "cut",
                "transition_out": "cut",
                "prompt_modifier": "on-the-scene journalistic b-roll footage, authentic reportage lighting, fast action",
                "ticker": "DEVELOPING STORY",
            },
            {
                "beat_type": "critical_detail",
                "title": "Key Supporting Detail",
                "proportion": 0.22,
                "camera_motion": "sharp_pan_right",
                "transition_in": "cut",
                "transition_out": "cut",
                "prompt_modifier": "relevant investigative data or subject b-roll, high information density, news graphic overlay",
                "ticker": "KEY EVIDENCE",
            },
            {
                "beat_type": "context_impact",
                "title": "Broader Impact & Analysis",
                "proportion": 0.20,
                "camera_motion": "quick_zoom_in",
                "transition_in": "cut",
                "transition_out": "cut",
                "prompt_modifier": "commentary context, wider press conference or analytical setting, serious tone",
                "ticker": "ANALYSIS & IMPACT",
            },
            {
                "beat_type": "sign_off",
                "title": "Wrap-up & Continuing Coverage",
                "proportion": 0.18,
                "camera_motion": "steady_center",
                "transition_in": "cut",
                "transition_out": "fade",
                "prompt_modifier": "studio broadcast sign-off, dynamic news ticker lower third, sharp professional finish",
                "ticker": "UPCOMING DEVELOPMENTS",
            },
        ]

        target_chunks = len(beat_definitions)
        script_chunks = split_script_into_chunks(brief.script, target_chunks)
        durations = allocate_durations(brief.target_duration_sec, [b["proportion"] for b in beat_definitions])

        scenes: List[SceneBeat] = []
        current_time = 0.0

        for i, (beat_def, chunk, dur) in enumerate(zip(beat_definitions, script_chunks, durations), start=1):
            start_t = round(current_time, 2)
            end_t = round(current_time + dur, 2)
            current_time = end_t

            ar_framing = "16:9 news broadcast format" if brief.aspect_ratio == "16:9" else "9:16 mobile live-report format"
            engineered_prompt = (
                f"{brief.title} - Beat {i}: {beat_def['title']}. "
                f"Content: {chunk[:80]}... "
                f"Aesthetic: {beat_def['prompt_modifier']}, {ar_framing}, realistic broadcast lighting, documentary grain."
            )

            scene = SceneBeat(
                scene_id=f"scene_{i:02d}",
                scene_index=i,
                title=beat_def["title"],
                beat_type=beat_def["beat_type"],
                narration_chunk=chunk,
                visual_prompt=engineered_prompt,
                duration_sec=dur,
                start_sec=start_t,
                end_sec=end_t,
                transition_in=beat_def["transition_in"],
                transition_out=beat_def["transition_out"],
                overlay_text=f"*** {beat_def['ticker']} *** {chunk[:45]}...",
                camera_motion=beat_def["camera_motion"],
                metadata={
                    "archetype": "news",
                    "ticker_status": beat_def["ticker"],
                    "aspect_ratio": brief.aspect_ratio,
                },
            )
            scenes.append(scene)

        plan_id = f"plan-{brief.id}-{brief_hash[:8]}"

        return ScenePlan(
            plan_id=plan_id,
            brief_id=brief.id,
            genre=brief.genre,
            aspect_ratio=brief.aspect_ratio,
            target_duration_sec=brief.target_duration_sec,
            planned_duration_sec=round(sum(s.duration_sec for s in scenes), 2),
            strategy_name=self.strategy_name,
            pacing_tempo=self.pacing_tempo,
            caption_treatment=self.caption_treatment,
            visual_strategy=self.visual_strategy,
            scenes=scenes,
            input_brief_hash=brief_hash,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
