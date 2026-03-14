# MindScope Scoring Model

MindScope estimates **overload risk** from passive desktop activity features. It does not diagnose stress or mental health conditions.

## Core Logic

1. Compute feature deviations from baseline using one-sided capped z-scores.
2. Convert deviations into three subscores:
   - Fragmentation
   - Focus instability
   - Interruption load
3. Combine subscores into a 0-100 overload score.
4. Find the nearest behavioral scenario centroid and apply a small adjustment.
5. Apply alert persistence rules only after multiple elevated windows.

## Directionality

- Higher is worse: `app_switch_count`, `distinct_app_count`, `afk_count`, `afk_minutes`, `work_context_entropy`, `work_reentry_count`
- Lower is worse: `focus_streak_minutes`

## Subscores

- Fragmentation = `0.45*switch_z + 0.25*distinct_z + 0.30*entropy_z`
- Focus instability = `0.65*focus_drop_z + 0.35*reentry_z`
- Interruption load = `0.60*afk_count_z + 0.40*afk_minutes_z`

Each raw subscore is scaled from `0-3` into `0-100`.

## Final Score

- `0.45*fragmentation + 0.35*focus_instability + 0.20*interruption`
- Scenario adjustments:
  - `overload`: `+8`
  - `admin_fragmented`: `+3`
  - `meeting_heavy`: `0`
  - `normal_work`: `0`
  - `deep_work`: `-10`
  - `procrastination`: `-5`

## Alert Rules

- Trigger after 3 consecutive windows above `70`
- Faster trigger after 2 consecutive windows above `85`

## Score Bands

- `0-39`: Normal
- `40-59`: Elevated
- `60-74`: High
- `75-100`: Sustained Overload Risk
