WITH player_stats AS (
  SELECT 
      gls.scorrer,
      tms.team as team_name,
      gls.team as team_id,
      COUNT(*) as goals
  FROM `table.degoals` as gls
  LEFT JOIN `table.teams` as tms ON gls.team = tms.team_id
  LEFT JOIN `table.srtdgms` as gms ON gls.game_id = gms.game_id AND gls.team = gms.team
  WHERE 
    ((gls.season > {season_start} AND gls.season < {season_end}) OR
     (gls.season = {season_start} AND gls.season = {season_end} AND gls.week >= {week_start} AND gls.week <= {week_end}) OR
     (gls.season = {season_start} AND gls.season < {season_end} AND gls.week >= {week_start}) OR
     (gls.season = {season_end} AND gls.season > {season_start} AND gls.week <= {week_end}))
    AND gls.comp_id IN ({comp})
    AND gls.team < 100
    AND gls.scorrer NOT IN ('טכני') 
    AND ({own_goals_condition})
    AND ({player_filter})
    AND ({team_filter})
    AND ({opp_filter})
    AND ({stadium_filter})
    AND ({side_filter})
    AND ({lctn_filter})
  GROUP BY gls.scorrer, team_name, team_id
),
player_totals AS (
  SELECT 
      scorrer,
      STRING_AGG(DISTINCT team_name, ', ' ORDER BY team_name) as all_teams,
      SUM(goals) as total_goals,
      COUNT(DISTINCT team_name) as team_count
  FROM player_stats
  GROUP BY scorrer
)
SELECT `שחקן`, `קבוצה`, `שערים`, is_summary, full_list, has_multiple FROM (
  SELECT 
      scorrer as `שחקן`,
      CAST(team_count AS STRING) || ' קבוצות' as `קבוצה`,
      total_goals as `שערים`,
      TRUE as is_summary,
      all_teams as full_list,
      team_count > 1 as has_multiple
  FROM player_totals 
  WHERE team_count > 1
  
  UNION ALL
  
  SELECT 
      p.scorrer as `שחקן`,
      p.team_name as `קבוצה`,
      p.goals as `שערים`,
      FALSE as is_summary,
      p.team_name as full_list,
      t.team_count > 1 as has_multiple
  FROM player_stats p
  JOIN player_totals t ON p.scorrer = t.scorrer
  WHERE 
    t.team_count = 1 
    OR {show_details_condition}
)
ORDER BY `שערים` DESC, `שחקן` ASC
{limit}