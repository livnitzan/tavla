WITH SeasonRules AS (
    -- שליפת חוקי העונה מהטבלה החדשה
    SELECT * FROM `table.szndct` WHERE season = {season}
),
RawGames AS (
    SELECT 
        s.team as team_id,
        s.season, s.week, s.date, s.gf, s.ga, s.res, 
        s.stage,
        CASE 
            WHEN s.res = 'W' THEN (SELECT CASE WHEN `3pt` THEN 3 ELSE 2 END FROM SeasonRules)
            WHEN s.res = 'D' AND s.forfeit IS NOT TRUE THEN 1
            ELSE 0 
        END as pts_earned
    FROM `table.srtdgms` s
    WHERE s.season = {season} 
      AND s.comp_id = 10 
      AND s.week <= {max_week}
      AND s.done IS TRUE
),
MaxDate AS (
    SELECT MAX(date) as last_game_date FROM RawGames
),
CupFinal AS (
    -- מציאת מנצחת ומפסידה מהמשחקים (stage 111)
    SELECT 
        MAX(date) as cup_date,
        MAX(CASE WHEN res = 'W' THEN team END) as winner_id,
        MAX(CASE WHEN res = 'L' THEN team END) as finalist_id
    FROM `table.srtdgms`
    WHERE season = {season} AND comp_id = 11 AND stage = 111 AND done IS TRUE
),
PointDeductions AS (
    SELECT team, SUM(pts) as total_deducted
    FROM `table.ddctn`
    WHERE season = {season} AND date <= (SELECT COALESCE(last_game_date, CURRENT_DATE()) FROM MaxDate)
    GROUP BY team
),
KizuzCalc AS (
    SELECT team_id,
        CASE 
            -- שימוש בעמודת kiz מהטבלה החדשה במקום בדיקה ידנית של שנים
            WHEN (SELECT IFNULL(kiz, FALSE) FROM SeasonRules) AND (SELECT MAX(week) FROM RawGames) >= 31 
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
    t.team_id,
    CONCAT(t.team, CASE WHEN COALESCE(pd.total_deducted, 0) != 0 THEN '*' ELSE '' END) as team_name,
    ms.gp, ms.wins, ms.draws, ms.losses, ms.gf_sum, ms.ga_sum,
    -- שובר שוויון לפי עמודת gd
    CASE 
        WHEN (SELECT IFNULL(gd, TRUE) FROM SeasonRules) THEN CAST(CAST((ms.gf_sum - ms.ga_sum) AS INT64) AS STRING)
        ELSE CAST(ROUND(SAFE_DIVIDE(CAST(ms.gf_sum AS FLOAT64), CAST(ms.ga_sum AS FLOAT64)), 2) AS STRING)
    END as goal_stat,
    CAST((kc.pts_base_after_kizuz + pc.pts_playoff - COALESCE(pd.total_deducted, 0)) AS INT64) as points,
    COALESCE(pd.total_deducted, 0) as penalty_val,
    ms.stage_val as stage_id,
    10 as comp_id,
    -- סכימת כל נציגות אירופה לטור אחד עבור קוד הפייתון הישן
    (COALESCE(CAST(sr.ucl AS INT64), 0) + COALESCE(CAST(sr.uel AS INT64), 0) + 
     COALESCE(CAST(sr.uecl AS INT64), 0) + COALESCE(CAST(sr.uch AS INT64), 0)) as uns,
    COALESCE(CAST(sr.uplf AS INT64), 0) as uplf,
    COALESCE(CAST(sr.mplf AS INT64), 0) as mplf,
    COALESCE(CAST(sr.rlg AS INT64), 0) as rlgt,
    COALESCE(CAST(sr.trl AS INT64), 0) as rtrl,
    COALESCE(CAST(sr.frz AS INT64), 0) as cncld,
    -- לוגיקת גביע (🏆)
    CASE 
        WHEN t.team_id = cf.winner_id AND (
            (cf.cup_date IS NOT NULL AND (SELECT MAX(date) FROM RawGames) >= cf.cup_date)
            OR {max_week} >= (SELECT IFNULL(weeks, 30) FROM SeasonRules)
        ) THEN t.team_id 
        ELSE NULL 
    END as cup_winner_id,
    -- נתונים נוספים ללוגיקת פיינליסטית ו-uch
    cf.finalist_id,
    COALESCE(CAST(sr.uch AS INT64), 0) as uch_val,
    (SELECT MAX(date) FROM RawGames) as current_max_date,
    cf.cup_date,
    (SELECT IFNULL(weeks, 30) FROM SeasonRules) as season_total_weeks
FROM `table.teams` t
JOIN MainStats ms ON t.team_id = ms.team_id
JOIN KizuzCalc kc ON t.team_id = kc.team_id
JOIN PlayoffCalc pc ON t.team_id = pc.team_id
LEFT JOIN PointDeductions pd ON t.team_id = pd.team
LEFT JOIN SeasonRules sr ON 1=1
LEFT JOIN CupFinal cf ON 1=1
WHERE t.team_id IN (SELECT DISTINCT team_id FROM RawGames)
ORDER BY 
    ms.stage_val ASC, 
    points DESC, 
    (CASE WHEN (SELECT IFNULL(gd, TRUE) FROM SeasonRules) THEN (ms.gf_sum - ms.ga_sum) ELSE SAFE_DIVIDE(ms.gf_sum, ms.ga_sum) END) DESC, 
    wins DESC