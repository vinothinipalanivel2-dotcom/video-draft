"""Product / Social archetype scene planning strategy."""

from datetime import datetime, timezone
from typing import List

from video_draft.planner.strategies.base import BaseArchetypeStrategy, allocate_durations, split_script_into_chunks
from video_draft.schema.brief import CreativeBrief
from video_draft.schema.scene_plan import SceneBeat, ScenePlan


class ProductStrategy(BaseArchetypeStrategy):
    """
    Product / Social archetype planning strategy.
    Prioritizes high aesthetic quality, punchy social hook-to-CTA rhythm,
    hero product framing, and kinetic headline callouts.
    """

    @property
    def genre(self) -> str:
        return "product"

    @property
    def strategy_name(self) -> str:
        return "ProductStrategy"

    @property
    def pacing_tempo(self) -> str:
        return "dynamic_punchy"

    @property
    def caption_treatment(self) -> str:
        return "kinetic_headline"

    @property
    def visual_strategy(self) -> str:
        return "commercial_hero_framing"

    def plan(self, brief: CreativeBrief, brief_hash: str) -> ScenePlan:
        # Commercial 4-beat structure: Hook -> Hero Feature -> Lifestyle Proof -> CTA
        beat_definitions = [
            {
                "beat_type": "visual_hook",
                "title": "Sensory Hook & First Impression",
                "proportion": 0.20,
                "camera_motion": "dynamic_macro_zoom",
                "transition_in": "fade",
                "transition_out": "wipe",
                "prompt_modifier": "high-end commercial macro teaser, dramatic rim lighting, premium material textures, sleek motion",
                "callout": "DISCOVER",
            },
            {
                "beat_type": "hero_reveal",
                "title": "Hero Feature Showcase",
                "proportion": 0.35,
                "camera_motion": "smooth_360_orbit",
                "transition_in": "wipe",
                "transition_out": "dissolve",
                "prompt_modifier": "flawless product hero shot, studio studio reflection, vibrant accents, 8k commercial showcase",
                "callout": "INNOVATION",
            },
            {
                "beat_type": "lifestyle_experience",
                "title": "Experience & Value Proof",
                "proportion": 0.25,
                "camera_motion": "sweeping_low_angle",
                "transition_in": "dissolve",
                "transition_out": "wipe",
                "prompt_modifier": "aspirational lifestyle environment, seamless interaction, radiant ambient lighting, premium lifestyle",
                "callout": "EXPERIENCE",
            },
            {
                "beat_type": "call_to_action",
                "title": "Call to Action & Brand Reveal",
                "proportion": 0.20,
                "camera_motion": "punchy_snap_zoom",
                "transition_in": "wipe",
                "transition_out": "fade",
                "prompt_modifier": "clean graphic endcard with hero silhouette, crisp typographic focus, striking brand identity finish",
                "callout": "AVAILABLE NOW",
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

            ar_framing = "vertical mobile reel composition 9:16" if brief.aspect_ratio == "9:16" else "wide cinematic commercial 16:9"
            engineered_prompt = (
                f"{brief.title} - Showcase Beat {i}: {beat_def['title']}. "
                f"Feature focus: {chunk[:80]}... "
                f"Commercial Style: {beat_def['prompt_modifier']}, {ar_framing}, studio lighting, pristine product aesthetics."
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
                overlay_text=f"// {beat_def['callout']} //",
                camera_motion=beat_def["camera_motion"],
                metadata={
                    "archetype": "product",
                    "commercial_phase": beat_def["beat_type"],
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
