# Scene Planner & Archetype Strategies

**Project**: `video-draft` (IncuBrix Track 03: Open-Source Draft Video Generation and Model Routing)  
**Module**: `video_draft.planner` (`scene_planner.py`, `strategies/`)  
**Schema**: `video_draft.schema.scene_plan` (`ScenePlan`, `SceneBeat`)

---

## 1. Scene Planner Responsibility

The `ScenePlanner` transforms a high-level creative brief (`CreativeBrief`) into a structured, deterministic, multi-scene timeline specification (`ScenePlan`).

### Core Invariants & Separation of Concerns
1. **Model-Agnostic Decomposition**: The Scene Planner does not hardcode generative models or select providers. It focuses exclusively on structural, narrative, pacing, and visual composition planning.
2. **Deterministic Segmentation**: Given the same creative brief, the planner produces identical scene beats, timestamps, prompts, overlay tags, and plan IDs.
3. **Sequential & Continuous Timings**: Scene indices are strictly monotonic ($1, 2, 3\dots$), and timestamps are gapless ($start_i = end_{i-1}$, $\sum \text{duration}_i = \text{target\_duration}$).
4. **Archetype-Driven Diversity**: Adapts scene count, pacing tempo, caption treatment, and visual prompt engineering according to the creative brief's genre.

```
[Creative Brief]
       |
       v
+--------------------------------------------------------------+
|                        SCENE PLANNER                         |
|  - Validates brief schema, script length, and duration bounds|
|  - Computes deterministic brief hash (SHA-256)               |
|  - Queries Strategy Registry for target genre                |
+------------------------------+-------------------------------+
                               |
       +-----------------------+-----------------------+
       |                       |                       |
       v                       v                       v
+---------------+       +---------------+       +---------------+
|   Education   |       |     News      |       |    Product    |
|   Strategy    |       |   Strategy    |       |   Strategy    |
| (Didactic, 4) |       |  (Urgent, 5)  |       |  (Punchy, 4)  |
+---------------+       +---------------+       +---------------+
       |                       |                       |
       +-----------------------+-----------------------+
                               |
                               v
                       [ScenePlan Output]
         (Ordered SceneBeats -> Feeds into Routing & Assembly)
```

---

## 2. Supported Archetypes & Strategy Matrix

The assessment requires three distinct archetypes with materially different workflows. The strategy pattern ensures that scene structure, pacing, caption treatment, and visual strategy change appropriately rather than merely altering the prompt.

| Feature | Education / Explainer | News / Commentary | Product / Social |
| :--- | :--- | :--- | :--- |
| **Strategy Class** | `EducationStrategy` | `NewsStrategy` | `ProductStrategy` |
| **Pacing Tempo** | `slow_didactic` | `fast_urgent` | `dynamic_punchy` |
| **Beat Count** | 4 Pedagogical Beats | 5 Rapid Cuts | 4 Commercial Beats |
| **Scene Duration Range** | $4.0\text{s} - 6.5\text{s}$ | $2.0\text{s} - 3.8\text{s}$ | $3.0\text{s} - 4.5\text{s}$ |
| **Transitions** | Dissolves / Smooth Fades | Hard Cuts / Sharp Edges | Directional Wipes / Snap Zooms |
| **Caption Treatment** | `explanatory_lower_third` (didactic topic badges) | `urgent_bottom_ticker` (running headline bar) | `kinetic_headline` (burst callouts) |
| **Visual Strategy** | `diagrammatic_didactic` | `b_roll_and_broadcast` | `commercial_hero_framing` |
| **Camera Motion** | Slow push-in, steady pan | Handheld dynamic, quick push | 360-orbit, macro zoom |

### 1. Education / Explainer Breakdown
1. **Intro & Problem Statement**: Overview schematic, establishes foundational problem context.
2. **Core Analytical Concept**: Detailed technical/conceptual diagram, clean studio illumination.
3. **Practical Demonstration**: Observable phenomenon in real-world scenario.
4. **Summary & Takeaway**: Synthesized visual conclusion with high conceptual clarity.

### 2. News / Commentary Breakdown
1. **Breaking Headline**: Newsroom anchor aesthetic with urgent headline framing.
2. **Primary Event & Facts**: On-the-scene journalistic b-roll footage.
3. **Key Supporting Detail**: High-density evidence and data visualization.
4. **Context & Impact**: Broader analytical context and interview setting.
5. **Broadcast Wrap-up**: Studio sign-off with continuing coverage metadata.

### 3. Product / Social Breakdown
1. **Sensory Hook**: High-end commercial teaser with dramatic rim lighting and textures.
2. **Hero Reveal**: 360-degree studio hero showcase emphasizing product aesthetics.
3. **Lifestyle Experience**: Seamless interaction in premium aspirational environments.
4. **Call to Action**: High-contrast graphic endcard and brand reveal.

---

## 3. Strategy Selection & Registry

Strategies inherit from `BaseArchetypeStrategy` and are registered in `src/video_draft/planner/strategies/__init__.py`:

```python
from video_draft.planner import get_strategy

# Deterministic strategy lookup
strategy = get_strategy("education")  # Returns EducationStrategy instance
```

If an unknown archetype is provided (e.g. `"vlog"`), the factory raises `UnsupportedArchetypeError`:
```text
UnsupportedArchetypeError: Unsupported archetype 'vlog'. Must be one of ['education', 'news', 'product'].
```

---

## 4. Scene Plan Output Structure

The generated `ScenePlan` contains high-level strategy metadata and an ordered list of `SceneBeat` objects:

```json
{
  "plan_id": "plan-brief-edu-001-a6998724",
  "brief_id": "brief-edu-001",
  "genre": "education",
  "aspect_ratio": "16:9",
  "target_duration_sec": 20.0,
  "planned_duration_sec": 20.0,
  "strategy_name": "EducationStrategy",
  "pacing_tempo": "slow_didactic",
  "caption_treatment": "explanatory_lower_third",
  "visual_strategy": "diagrammatic_didactic",
  "scenes": [
    {
      "scene_id": "scene_01",
      "scene_index": 1,
      "title": "Hook & Problem Statement",
      "beat_type": "intro_problem",
      "narration_chunk": "In 1916, Albert Einstein predicted ripples in spacetime...",
      "visual_prompt": "Introduction to Gravitational Waves - Scene 1: Hook & Problem Statement...",
      "duration_sec": 4.4,
      "start_sec": 0.0,
      "end_sec": 4.4,
      "transition_in": "fade",
      "transition_out": "dissolve",
      "overlay_text": "[OVERVIEW] Hook & Problem Statement",
      "camera_motion": "slow_push_in",
      "metadata": { "archetype": "education", "aspect_ratio": "16:9" }
    }
  ],
  "input_brief_hash": "e7a0d5270d9858beac15f886fd0eaca6c4a247d1e1329d260f0281121cc7f1c1",
  "created_at": "2026-09-06T17:41:12.645560+00:00"
}
```

---

## 5. Validation and Error Handling

The planner validates both input constraints and output structural integrity:

| Validation Condition | Error Type | Action Taken |
| :--- | :--- | :--- |
| Non-`CreativeBrief` input | `PlannerValidationError` | Rejects input with explicit type message |
| Empty / whitespace-only script | `PlannerValidationError` | Rejects brief before strategy execution |
| Script $< 10$ characters | `PlannerValidationError` | Requires minimum narrative substance |
| Duration $< 15\text{s}$ or $> 30\text{s}$ | `PlannerValidationError` | Enforces IncuBrix 15–30s draft constraints |
| Aspect ratio not in `16:9`, `9:16` | `PlannerValidationError` | Enforces supported geometry |
| Unrecognized archetype | `UnsupportedArchetypeError` | Controlled rejection with supported genres |
| Discontinuous scene timestamps | `Pydantic ValidationError` | Enforced at schema level ($start_i == end_{i-1}$) |
| Duration sum drift | `Pydantic ValidationError` | Guaranteed $\sum \text{duration}_i == \text{planned\_duration}$ |

---

## 6. Integration with Phase 2 Routing Engine

Phase 3 integrates directly with the Phase 2 router:
```python
from video_draft.planner import plan_scenes
from video_draft.router import route

# 1. Plan scene breakdown
scene_plan = plan_scenes(brief)

# 2. Feed scene plan into model routing
decision = route(creative_brief=brief, scene_plan=scene_plan)
```
When `scene_plan` is passed to `route(...)`:
- The router evaluates candidate models' `max_duration_sec` against the longest planned scene beat ($\max(s.\text{duration\_sec})$) rather than an estimated average.
- If `scene_plan` is omitted, the router gracefully defaults to estimated pacing, preserving 100% backwards compatibility with Phase 2.
