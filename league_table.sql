WITH RawGames AS (
    SELECT 
        s.team as team_id,
        s.season, s.week, s.date, s.gf, s.ga, s.res, 
        s.stage,
        CASE 
            WHEN s.res = 'W' THEN (CASE WHEN s.season <= 1982 THEN 2 ELSE 3 END)
            WHEN s.res = 'D' AND s.forfeit IS NOT TRUE THEN 1
            ELSE 0 
        END as pts_earned
    FROM `table.srtdgms` s
    WHERE s.season = {season} 
      AND s.comp_id = 10 
      AND s.week <= {max_week}
      -- תיקו סוג הנתונים: השוואה בין TIMESTAMP ל-TIMESTAMP
      AND TIMESTAMP(DATETIME(s.date, COALESCE(s.time, TIME '00:00:00'))) <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 135 MINUTE)
),
MaxDate AS (
    SELECT MAX(date) as last_game_date FROM RawGames
),
PointDeductions AS (
    SELECT team, SUM(pts) as total_deducted
    FROM `table.ddctn`
    WHERE season = {season} AND date <= (SELECT COALESCE(last_game_date, CAST(CURRENT_DATE() AS DATE)) FROM MaxDate)
    GROUP BY team
),
KizuzCalc AS (
    SELECT team_id,
        CASE 
            WHEN {season} IN (2010, 2011) AND (SELECT MAX(week) FROM RawGames) >= 31 
            THEN CEIL(SUM(CASE WHEN week <= 30 THEN pts_earned ELSE 0 END) / 2.0)
            ELSE SUM(CASE WHEN week <= 30 THEN pts_earned ELSE 0 END)
        END as pts_base_after_kizuz
    FROM RawGames GROUP BY team_id
),
PlayoffCalc AS (
    SELECT team_id, SUM(CASE WHEN week > 30 THEN pts_earned ELSE 0 END) as pts_playoff
    FROM RawGames GROUP BY team_id
),
MainStats AS (
    SELECT team_id, COUNT(*) as gp, COUNTIF(res = 'W') as wins, COUNTIF(res = 'D') as draws,
        COUNTIF(res = 'L') as losses, SUM(gf) as gf_sum, SUM(ga) as ga_sum, MAX(stage) as stage_val
    FROM RawGames GROUP BY team_id
)
SELECT 
    CONCAT(t.team, CASE WHEN COALESCE(pd.total_deducted, 0) != 0 THEN '*' ELSE '' END) as team_name,
    ms.gp, ms.wins, ms.draws, ms.losses, ms.gf_sum, ms.ga_sum,
    CASE 
        WHEN {season} >= 1970 THEN CAST(CAST((ms.gf_sum - ms.ga_sum) AS INT64) AS STRING)
        ELSE CAST(ROUND(SAFE_DIVIDE(CAST(ms.gf_sum AS FLOAT64), CAST(ms.ga_sum AS FLOAT64)), 2) AS STRING)
    END as goal_stat,
    CAST((kc.pts_base_after_kizuz + pc.pts_playoff - COALESCE(pd.total_deducted, 0)) AS INT64) as points,
    COALESCE(pd.total_deducted, 0) as penalty_val
FROM `table.teams` t
JOIN MainStats ms ON t.team_id = ms.team_id
JOIN KizuzCalc kc ON t.team_id = kc.team_id
JOIN PlayoffCalc pc ON t.team_id = pc.team_id
LEFT JOIN PointDeductions pd ON t.team_id = pd.team
WHERE t.team_id IN (SELECT DISTINCT team_id FROM RawGames)
ORDER BY 
    (CASE WHEN (SELECT MAX(week) FROM RawGames) >= 31 THEN ms.stage_val ELSE 0 END) ASC,
    points DESC,
    CASE WHEN {season} >= 1970 THEN (ms.gf_sum - ms.ga_sum) ELSE SAFE_DIVIDE(ms.gf_sum, ms.ga_sum) END DESC,
    wins DESC,
    gf_sum DESC
