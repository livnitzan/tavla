WITH MaxSeason AS (
  SELECT MAX(season) as current_season FROM `table.srtdgms`
),
MatchStatus AS (
  SELECT 
    m.game_id, m.team as team_id, m.rival as rival_id, t_rival.team as rival_name,
    m.date, m.week, m.res, m.gf, m.ga, m.lctn, m.season, m.comp_id,
    m.hglts,
    CASE WHEN {action_conditions} THEN 1 ELSE 0 END as is_streak_match,
    ROW_NUMBER() OVER(PARTITION BY m.team ORDER BY m.date) as row_num_total,
    MAX(m.date) OVER(PARTITION BY m.team) as last_team_game_date,
    LEAD(t_rival.team) OVER(PARTITION BY m.team ORDER BY m.date) as next_rival,
    LEAD(m.week) OVER(PARTITION BY m.team ORDER BY m.date) as next_week,
    LEAD(m.season) OVER(PARTITION BY m.team ORDER BY m.date) as next_season,
    LEAD(m.gf) OVER(PARTITION BY m.team ORDER BY m.date) as next_gf,
    LEAD(m.ga) OVER(PARTITION BY m.team ORDER BY m.date) as next_ga,
    LEAD(m.hglts) OVER(PARTITION BY m.team ORDER BY m.date) as next_hglts,
    LEAD(m.date) OVER(PARTITION BY m.team ORDER BY m.date) as next_date,
    LAG(t_rival.team) OVER(PARTITION BY m.team ORDER BY m.date) as prev_rival,
    LAG(m.week) OVER(PARTITION BY m.team ORDER BY m.date) as prev_week,
    LAG(m.season) OVER(PARTITION BY m.team ORDER BY m.date) as prev_season,
    LAG(m.gf) OVER(PARTITION BY m.team ORDER BY m.date) as prev_gf,
    LAG(m.ga) OVER(PARTITION BY m.team ORDER BY m.date) as prev_ga,
    LAG(m.hglts) OVER(PARTITION BY m.team ORDER BY m.date) as prev_hglts,
    LAG(m.date) OVER(PARTITION BY m.team ORDER BY m.date) as prev_date
  FROM `table.srtdgms` m
  JOIN `table.teams` t_rival ON m.rival = t_rival.team_id
  WHERE m.team < 100 
    AND m.forfeit IS NOT TRUE 
    AND m.res IS NOT NULL
    AND m.done IS TRUE
    AND {frame_conditions}
    {team_filter}
),
GroupedStreaks AS (
  SELECT 
    *,
    row_num_total - ROW_NUMBER() OVER(
        PARTITION BY team_id, is_streak_match, {scope_partition} 
        ORDER BY date
    ) as streak_id
  FROM MatchStatus
),
StreaksSummary AS (
  SELECT 
    team_id, 
    streak_id,
    {scope_partition} as partition_val,
    COUNT(*) as streak_length, 
    MIN(date) as start_date, 
    MAX(date) as end_date,
    MAX(last_team_game_date) as team_last_date,
    MAX(season) as end_season,
    MIN(season) as start_season,
    MIN(row_num_total) as streak_start_row,
    ARRAY_AGG(STRUCT(rival_name, week, season, gf, ga, hglts, date, res) ORDER BY date ASC) as streak_matches,
    ARRAY_AGG(STRUCT(next_rival, next_week, next_season, next_gf, next_ga, next_hglts, next_date) ORDER BY date DESC LIMIT 1)[OFFSET(0)] as next_info,
    ARRAY_AGG(STRUCT(prev_rival, prev_week, prev_season, prev_gf, prev_ga, prev_hglts, prev_date) ORDER BY date ASC LIMIT 1)[OFFSET(0)] as prev_info
  FROM GroupedStreaks
  WHERE is_streak_match = 1
  GROUP BY team_id, streak_id, partition_val
),
FinalResults AS (
    SELECT 
        t.team as `קבוצה`,
        s.streak_length as `רצף`,
        CASE 
            WHEN s.start_season = s.end_season THEN CAST(s.start_season AS STRING)
            ELSE CONCAT(CAST(s.start_season AS STRING), '-', CAST(s.end_season AS STRING))
        END as `עונות`,
        s.start_date,
        s.end_date,
        CASE 
          WHEN s.end_date = s.team_last_date AND s.end_season = (SELECT current_season FROM MaxSeason) 
          THEN '✅' ELSE '❌' 
        END as `פעיל`,
        s.streak_matches,
        s.prev_info,
        s.next_info,
        s.end_season as season,
        s.streak_start_row,
        (SELECT MIN(row_num_total) FROM MatchStatus m2 WHERE m2.team_id = s.team_id AND m2.season = s.end_season) as first_game_row_in_season
    FROM StreaksSummary s
    JOIN `table.teams` t ON s.team_id = t.team_id
)
SELECT * FROM FinalResults
WHERE `רצף` >= 1 
{active_only_filter}
{scope_final_filter}
ORDER BY `רצף` DESC, end_date DESC
LIMIT 100