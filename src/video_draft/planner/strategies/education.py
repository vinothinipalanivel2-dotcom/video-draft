"""Education / Explainer archetype scene planning strategy."""

from datetime import datetime, timezone
from typing import List

from video_draft.planner.strategies.base import BaseArchetypeStrategy, allocate_durations, split_script_into_chunks
from video_draft.schema.brief import CreativeBrief
from video_draft.schema.scene_plan import SceneBeat, ScenePlan


class EducationStrategy(BaseArchetypeStrategy):
    """
    Education / Explainer archetype planning strategy.
    Prioritizes conceptual clarity, deliberate pacing, structured pedagogical beats,
    and explanatory lower-third concept annotations.
    """

    @property
    def genre(self) -> str:
        return "education"

    @property
    def strategy_name(self) -> str:
        return "EducationStrategy"

    @property
    def pacing_tempo(self) -> str:
        return "slow_didactic"

    @property
    def caption_treatment(self) -> str:
        return "explanatory_lower_third"

    @property
    def visual_strategy(self) -> str:
        return "diagrammatic_didactic"

    def plan(self, brief: CreativeBrief, brief_hash: str) -> ScenePlan:
        # Pedagogical 4-beat structure: Hook -> Concept Breakdown -> Application -> Summary
        beat_definitions = [
            {
                "beat_type": "intro_problem",
                "title": "Hook & Problem Statement",
                "proportion": 0.22,
                "camera_motion": "slow_push_in",
                "transition_in": "fade",
                "transition_out": "dissolve",
                "prompt_modifier": "clear schematic overview, establishing focal subject, educational documentary aesthetic",
                "tag": "OVERVIEW",
            },
            {
                "beat_type": "core_breakdown",
                "title": "Core Analytical Concept",
                "proportion": 0.32,
                "camera_motion": "steady_pan",
                "transition_in": "dissolve",
                "transition_out": "dissolve",
                "prompt_modifier": "detailed anatomical or technical diagram, high clarity, clean studio illumination",
                "tag": "KEY CONCEPT",
            },
            {
                "beat_type": "demonstration",
                "title": "Practical Demonstration & Evidence",
                "proportion": 0.26,
                "camera_motion": "slow_track_right",
                "transition_in": "dissolve",
                "transition_out": "dissolve",
                "prompt_modifier": "observable phenomenon in action, real-world context, measured motion dynamics",
                "tag": "ANALYSIS",
            },
            {
                "beat_type": "summary_takeaway",
                "title": "Summary & Key Takeaway",
                "proportion": 0.20,
                "camera_motion": "slow_pull_back",
                "transition_in": "dissolve",
                "transition_out": "fade",
                "prompt_modifier": "synthesized visual conclusion, memorable visual emblem, quiet confident framing",
                "tag": "SUMMARY",
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

            # Engineer visual prompt tailored for educational clarity and aspect ratio
            ar_framing = "wide cinematic framing 16:9" if brief.aspect_ratio == "16:9" else "vertical balanced composition 9:16"
            engineered_prompt = (
                f"{brief.title} - Scene {i}: {beat_def['title']}. "
                f"Visual depiction: {chunk[:80]}... "
                f"Style: {beat_def['prompt_modifier']}, {ar_framing}, high clarity, didactic visual focus."
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
                overlay_text=f"[{beat_def['tag']}] {beat_def['title']}",
                camera_motion=beat_def["camera_motion"],
                metadata={
                    "archetype": "education",
                    "pedagogical_role": beat_def["beat_type"],
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
