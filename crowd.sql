SELECT 
    m.game_id,
    m.season,
    m.week,
    m.date,
    t.team AS team_name,
    r.team AS rival_name,
    s.stadium,
    m.res,
    m.gf,
    m.ga,
    m.tcrowd,
    m.rcrowd,
    m.team AS team_id,
    m.rival AS rival_id,
    m.stad_id,
    tz.stad_id AS original_home_stad
FROM `tavla-440015.table.srtdgms` m
JOIN `tavla-440015.table.teams` t ON m.team = t.team_id
JOIN `tavla-440015.table.teams` r ON m.rival = r.team_id
JOIN `tavla-440015.table.stads` s ON m.stad_id = s.stad_id
LEFT JOIN `tavla-440015.table.tmszn2` tz ON m.team = tz.team_id AND m.season = tz.season
WHERE m.tcrowd IS NOT NULL 
  AND m.lctn = 'H'
  AND m.comp_id = 10
  AND m.season BETWEEN {season_start} AND {season_end}
  AND m.week BETWEEN {week_start} AND {week_end}