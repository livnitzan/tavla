WITH season_stats AS (
  SELECT 
      tms.team as team_name,
      gms.season
  FROM `table.srtdgms` as gms
  LEFT JOIN `table.teams` as tms ON gms.team = tms.team_id
  WHERE gms.comp_id = 10
    AND gms.done IS TRUE
  GROUP BY ALL -- במקום לפרט team_name, season
  HAVING {conditions}
),
summary AS (
  SELECT 
      COUNT(*) as total_cases,
      MIN(season) as first_season,
      MAX(season) as last_season
  FROM season_stats
),
last_teams AS (
  SELECT 
      STRING_AGG(team_name, ', ') as teams_list
  FROM season_stats
  WHERE season = (SELECT last_season FROM summary)
),
counts_per_team AS (
  SELECT 
      team_name, 
      COUNT(*) as occurrence_count
  FROM season_stats
  GROUP BY ALL -- קיבוץ אוטומטי לפי שם הקבוצה
),
grouped_counts AS (
  SELECT 
      occurrence_count,
      STRING_AGG(team_name, ', ' ORDER BY team_name) as teams
  FROM counts_per_team
  GROUP BY ALL -- קיבוץ אוטומטי לפי מספר המופעים
)
SELECT 
    s.team_name as `קבוצה`, 
    s.season as `עונה`,
    (SELECT 'נמצאו ' || CAST(total_cases AS STRING) || ' מקרים כאלה בליגת העל מאז עונת ' || CAST(first_season AS STRING) || 
     ', הפעם האחרונה של קבוצות ' || teams_list || ' בעונת ' || CAST(last_season AS STRING) FROM summary, last_teams) as summary_text,
    gc.occurrence_count as `מספר מקרים`,
    gc.teams as `קבוצות`
FROM season_stats s
LEFT JOIN grouped_counts gc ON 1=1
ORDER BY s.season DESC, s.team_name ASC