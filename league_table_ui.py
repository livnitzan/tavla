import streamlit as st
import pandas as pd
import numpy as np

def show_league_table_interface(client, sql_template_raw, get_season_data, current_team):
    st.markdown("<h1 style='text-align: center; font-weight: 400; color: #2c3e50; font-family: sans-serif; margin-bottom: 25px;'>טבלת הליגה</h1>", unsafe_allow_html=True)

    season_dict = get_season_data()
    season_options = sorted(list(season_dict.keys()), reverse=True)

    _, col_a, col_b, _ = st.columns([2, 1, 1, 2])
    with col_a:
        selected_season = st.selectbox("בחר עונה:", season_options, index=0, key="league_season_sel")
    with col_b:
        max_w_from_dict = season_dict.get(selected_season, 30)
        selected_week = st.number_input("עד מחזור:", 1, max_w_from_dict, max_w_from_dict, key="league_week_sel")

    sql_query = f"""
    WITH SeasonRules AS (
        SELECT * FROM `table.szndct` WHERE season = {selected_season}
    ),
    RawGames AS (
        SELECT 
            s.team as team_id, s.season, s.week, s.date, s.gf, s.ga, s.res, s.stage,
            t_rival.team as rival_name,
            CASE 
                WHEN s.res = 'W' THEN (SELECT CASE WHEN IFNULL(`3pt`, TRUE) THEN 3 ELSE 2 END FROM SeasonRules)
                WHEN s.res = 'D' AND s.forfeit IS NOT TRUE THEN 1
                ELSE 0 
            END as pts_earned
        FROM `table.srtdgms` s
        JOIN `table.teams` t_rival ON s.rival = t_rival.team_id
        WHERE s.season = {selected_season} AND s.comp_id = 10 AND s.week <= {selected_week} AND s.done IS TRUE
    ),
    FormCalc AS (
        SELECT team_id, 
               STRING_AGG(CONCAT(res, '|', rival_name, '|', gf, '-', ga), ';' ORDER BY date DESC LIMIT 5) as last_5_detailed
        FROM RawGames
        GROUP BY team_id
    ),
    CupFinal AS (
        SELECT 
            MAX(date) as cup_date,
            MAX(CASE WHEN res = 'W' OR (res = 'D' AND tbreak IS NOT NULL) THEN team END) as winner_id,
            MAX(CASE WHEN res = 'L' OR (res = 'D' AND tbreak IS NULL) THEN team END) as loser_id
        FROM `table.srtdgms`
        WHERE season = {selected_season} AND comp_id = 11 AND stage = 111 AND done IS TRUE
    ),
    MaxDateInSelection AS (
        SELECT MAX(date) as current_max_date FROM RawGames
    ),
    PointDeductions AS (
        SELECT team, SUM(pts) as total_deducted FROM `table.ddctn`
        WHERE season = {selected_season} AND date <= (SELECT COALESCE(MAX(date), CURRENT_DATE()) FROM RawGames)
        GROUP BY team
    ),
    MainStats AS (
        SELECT team_id, COUNT(*) as gp, COUNTIF(res = 'W') as wins, COUNTIF(res = 'D') as draws,
            COUNTIF(res = 'L') as losses, SUM(gf) as gf_sum, SUM(ga) as ga_sum, MAX(stage) as stage_val
        FROM RawGames GROUP BY team_id
    ),
    KizuzCalc AS (
        SELECT team_id,
            CASE 
                WHEN (SELECT IFNULL(kiz, FALSE) FROM SeasonRules) AND (SELECT MAX(week) FROM RawGames) >= 31 
                THEN CEIL(SUM(CASE WHEN week <= 30 THEN pts_earned ELSE 0 END) / 2.0)
                ELSE SUM(CASE WHEN week <= 30 THEN pts_earned ELSE 0 END)
            END as pts_base_after_kizuz
        FROM RawGames GROUP BY team_id
    ),
    PlayoffCalc AS (
        SELECT team_id, SUM(CASE WHEN week > 30 THEN pts_earned ELSE 0 END) as pts_playoff
        FROM RawGames GROUP BY team_id
    )
    SELECT 
        t.team_id, t.team as team_name_raw,
        CASE WHEN COALESCE(pd.total_deducted, 0) != 0 THEN CONCAT(t.team, '*') ELSE t.team END as team_display_name,
        CASE 
            WHEN cf.winner_id IS NOT NULL AND t.team_id = cf.winner_id 
                 AND ((SELECT current_max_date FROM MaxDateInSelection) >= cf.cup_date OR {selected_week} >= (SELECT IFNULL(weeks, 30) FROM SeasonRules))
            THEN TRUE ELSE FALSE 
        END AS is_cup_winner,
        CASE WHEN cf.loser_id IS NOT NULL AND t.team_id = cf.loser_id THEN TRUE ELSE FALSE END as is_cup_loser,
        ms.gp, ms.wins, ms.draws, ms.losses, ms.gf_sum, ms.ga_sum,
        CAST((kc.pts_base_after_kizuz + pc.pts_playoff - COALESCE(pd.total_deducted, 0)) AS INT64) as points,
        COALESCE(CAST(sr.ucl AS INT64), 0) as ucl_s, COALESCE(CAST(sr.uch AS INT64), 0) as uch_s,
        COALESCE(CAST(sr.uel AS INT64), 0) as uel_s, COALESCE(CAST(sr.uecl AS INT64), 0) as uecl_s,
        COALESCE(CAST(sr.rlg AS INT64), 0) as rlgt, COALESCE(CAST(sr.trl AS INT64), 0) as rtrl,
        COALESCE(CAST(sr.uplf AS INT64), 0) as uplf, COALESCE(CAST(sr.mplf AS INT64), 0) as mplf,
        COALESCE(CAST(sr.weeks AS INT64), 30) as max_weeks, IFNULL(sr.`3pt`, TRUE) as is_3pt,
        ms.stage_val as stage_id, IFNULL(sr.gd, TRUE) as is_gd_rule,
        CASE 
            WHEN (SELECT IFNULL(gd, TRUE) FROM SeasonRules) THEN CAST(CAST((ms.gf_sum - ms.ga_sum) AS INT64) AS STRING)
            ELSE CAST(ROUND(SAFE_DIVIDE(CAST(ms.gf_sum AS FLOAT64), CAST(ms.ga_sum AS FLOAT64)), 2) AS STRING)
        END as goal_stat,
        COALESCE(pd.total_deducted, 0) as total_deducted,
        fc.last_5_detailed
    FROM `table.teams` t
    JOIN MainStats ms ON t.team_id = ms.team_id
    JOIN KizuzCalc kc ON t.team_id = kc.team_id
    JOIN PlayoffCalc pc ON t.team_id = pc.team_id
    JOIN FormCalc fc ON t.team_id = fc.team_id
    LEFT JOIN PointDeductions pd ON t.team_id = pd.team
    LEFT JOIN SeasonRules sr ON 1=1
    CROSS JOIN CupFinal cf
    WHERE t.team_id IN (SELECT DISTINCT team_id FROM RawGames)
    ORDER BY ms.stage_val ASC, points DESC, (CASE WHEN is_gd_rule THEN (ms.gf_sum - ms.ga_sum) ELSE SAFE_DIVIDE(ms.gf_sum, ms.ga_sum) END) DESC, wins DESC
    """

    try:
        df = client.query(sql_query).to_dataframe()
        if not df.empty:
            df = df.replace({np.nan: None})
            d = df.iloc[0]
            ucl_s, uch_s, uel_s, uecl_s = int(d['ucl_s']), int(d['uch_s']), int(d['uel_s']), int(d['uecl_s'])
            rlgt, rtrl, total_teams = int(d['rlgt']), int(d['rtrl']), len(df)
            uplf, mplf = int(d['uplf']), int(d['mplf'])
            max_weeks, is_3pt = int(d['max_weeks']), bool(d['is_3pt'])
            pts_win = 3 if is_3pt else 2
            goal_label = "הפרש" if bool(d.get('is_gd_rule', True)) else "יחס"

            def get_form_html(form_str):
                if not form_str: return ""
                games = form_str.split(';')
                html = '<div class="form-wrapper">'
                colors = {'W': '#2ecc71', 'D': '#f1c40f', 'L': '#e74c3c'}
                
                for game in games:
                    parts = game.split('|')
                    if len(parts) < 3: continue
                    res, rival, score = parts[0], parts[1], parts[2]
                    color = colors.get(res, '#eee')
                    
                    # הפיכת סדר התוצאה: אם קיבלנו "2-1", נהפוך ל-"1-2"
                    # כך שבתצוגה מימין לשמאל זה ייראה נכון
                    score_parts = score.split('-')
                    if len(score_parts) == 2:
                        reversed_score = f"{score_parts[1]}-{score_parts[0]}"
                    else:
                        reversed_score = score

                    # שימוש בקידוד ישות HTML למרכאות כפולות
                    clean_rival = rival.replace('"', '&quot;')
                    tooltip_text = f"{clean_rival} {reversed_score}"
                    
                    html += f'<div class="form-dot" style="background-color: {color};" data-text="{tooltip_text}"></div>'
                html += '</div>'
                return html

            st.markdown("""
                <style>
                    div[data-testid="column"] > div { display: flex; justify-content: center; }
                    div[data-testid="stCheckbox"] > label { flex-direction: row-reverse; gap: 8px; width: auto; justify-content: center; }
                    [data-testid="stVerticalBlock"] { gap: 0.5rem; }
                    .block-container { padding-top: 2rem; }

                    .playoff-label-container { text-align: right; margin-top: 20px; margin-bottom: 15px; font-weight: 600; font-size: 14px; color: #444; font-family: sans-serif; }
                    .league-table { width: 100%; border-collapse: collapse; direction: rtl; font-family: sans-serif; table-layout: fixed; margin-top: 0px; }
                    .header-row { border-bottom: 1px solid #eee; }
                    .header-cell { padding: 8px 2px; text-align: center; font-size: 13px; color: #999; font-weight: 500; }
                    .league-table td { padding: 10px 2px; border-bottom: 1px solid #f2f2f2; text-align: center; font-size: 14px; color: #333; }
                    .row-champion { background-color: #f0f7ff !important; }
                    .row-relegation { background-color: #fff8f8 !important; }
                    .row-playoff { background-color: #fffef2 !important; }
                    .team-cell { text-align: right !important; padding-right: 22px !important; position: relative; overflow: visible !important; }
                    
                    .bar-container { position: absolute; right: 0; top: 0; bottom: 0; display: flex; flex-direction: row-reverse; gap: 1px; }
                    .bar { width: 4px; height: 100%; }
                    .bar-gold { background-color: rgba(241, 196, 15, 0.7); } 
                    .bar-champ { background-color: rgba(41, 128, 185, 0.9); }
                    .bar-relegated { background-color: #e74c3c; }

                    .corner-left { position: absolute; top: 0; left: 0; width: 0; height: 0; border-style: solid; z-index: 10; border-width: 12px 12px 0 0; }
                    .tri-ucl { border-color: rgba(52, 152, 219, 0.6) transparent transparent transparent; }
                    .tri-uch { border-color: rgba(230, 126, 34, 0.6) transparent transparent transparent; }
                    .tri-uel { border-color: rgba(155, 89, 182, 0.6) transparent transparent transparent; }
                    .tri-uclf { border-color: rgba(46, 204, 113, 0.6) transparent transparent transparent; }
                    
                    .stat-cell-ltr { direction: ltr !important; unicode-bidi: bidi-override; }
                    .rank-cell { color: #ccc; width: 40px; }
                    .deduction-note { text-align: right; color: #888; font-size: 14px; margin-top: 10px; }
                    .clinch-bold { font-weight: bold !important; }

                    /* --- Tooltip CSS --- */
                    .form-wrapper { display: flex; gap: 4px; justify-content: center; direction: ltr; }
                    .form-dot { 
                        width: 10px; height: 10px; border-radius: 50%; 
                        transition: transform 0.2s; cursor: pointer;
                        position: relative;
                    }
                    .form-dot:hover { transform: scale(1.3); }
                    
                    .form-dot:hover::after {
                        content: attr(data-text);
                        position: absolute;
                        bottom: 18px;
                        left: 50%;
                        transform: translateX(-50%);
                        background-color: #2c3e50;
                        color: #fff;
                        padding: 5px 10px;
                        border-radius: 6px;
                        font-size: 12px;
                        white-space: nowrap;
                        z-index: 9999;
                        pointer-events: none;
                        font-family: sans-serif;
                    }
                    
                    .form-dot:hover::before {
                        content: '';
                        position: absolute;
                        bottom: 12px;
                        left: 50%;
                        transform: translateX(-50%);
                        border-width: 6px;
                        border-style: solid;
                        border-color: #2c3e50 transparent transparent transparent;
                        z-index: 9999;
                        pointer-events: none;
                    }
                </style>
            """, unsafe_allow_html=True)

            _, c_mid_a, c_mid_b, c_mid_c, _ = st.columns([2, 0.7, 0.7, 1, 2])
            with c_mid_a: show_stats = st.toggle("מאזן", key="t_stats_v54")
            with c_mid_b: show_goals = st.toggle("שערים", key="t_goals_v54")
            with c_mid_c: show_form = st.toggle("5 אחרונים", value=True, key="t_form_v54")

            c_spacer, c_main, _ = st.columns([1, 4, 1])
            with c_main:
                def build_table_only(data_part, start_idx, is_bottom_playoff=False):
                    html = f'<table class="league-table"><thead><tr class="header-row"><th class="header-cell rank-cell">#</th><th class="header-cell" style="text-align:right; padding-right:15px;">קבוצה</th>'
                    if show_stats: html += '<th class="header-cell">נצ\'</th><th class="header-cell">תי\'</th><th class="header-cell">הפ\'</th>'
                    if show_goals: html += '<th class="header-cell">זכות</th><th class="header-cell">חובה</th>'
                    html += f'<th class="header-cell">מש\'</th><th class="header-cell">{goal_label}</th><th class="header-cell">נק\'</th>'
                    if show_form: html += '<th class="header-cell" style="width:85px;">פורמה</th>'
                    html += '</tr></thead><tbody>'
                    
                    cur_max = (max_weeks - 3) if is_bottom_playoff else max_weeks
                    w_left = max(0, cur_max - selected_week)
                    potential = w_left * pts_win
                    
                    winner_row = df[df['is_cup_winner'] == True]
                    cup_id = winner_row['team_id'].iloc[0] if not winner_row.empty else None
                    loser_id = df[df['is_cup_loser'] == True]['team_id'].iloc[0] if any(df['is_cup_loser']) else None
                    
                    slots = []
                    for r in range(1, ucl_s + 1): slots.append((r, "tri-ucl"))
                    uch_team_id = None
                    if uch_s > 0 and cup_id:
                        uch_team_id = loser_id if (cup_id == df.iloc[0]['team_id']) else cup_id
                        try: uch_rank = df[df['team_id'] == uch_team_id].index[0] + 1; slots.append((uch_rank, "tri-uch"))
                        except: pass
                    
                    uel_rem = uel_s
                    if uch_s == 0 and uel_s > 0:
                        if cup_id:
                            cup_rank = df[df['team_id'] == cup_id].index[0] + 1
                            if cup_rank > ucl_s: slots.append((cup_rank, "tri-uel")); uel_rem -= 1
                        else: uel_rem -= 1
                    
                    uel_assigned = 0
                    for r in range(2, total_teams + 1):
                        if uel_assigned >= uel_rem: break
                        t_id = df.iloc[r-1]['team_id']
                        if r <= ucl_s or t_id == uch_team_id or t_id == cup_id: continue
                        slots.append((r, "tri-uel")); uel_assigned += 1

                    uecl_rem = uecl_s
                    if uel_s == 0 and uecl_s > 0:
                        if cup_id:
                            cup_rank = df[df['team_id'] == cup_id].index[0] + 1
                            if cup_rank > ucl_s: slots.append((cup_rank, "tri-uclf")); uecl_rem -= 1
                        else: uecl_rem -= 1
                    
                    uecl_assigned = 0
                    for r in range(2, total_teams + 1):
                        if uecl_assigned >= uecl_rem: break
                        if any(s[0] == r for s in slots): continue
                        slots.append((r, "tri-uclf")); uecl_assigned += 1

                    safe_idx = total_teams - rlgt - rtrl - 1
                    pts_to_safety = int(df.iloc[safe_idx]['points']) if safe_idx >= 0 else 0

                    for i, (_, row) in enumerate(data_part.iterrows()):
                        rank = start_idx + i
                        is_rel = (rlgt > 0 and rank > total_teams - rlgt)
                        is_ply = (rtrl > 0 and rank > total_teams - rlgt - rtrl and rank <= total_teams - rlgt)
                        row_class = "row-champion" if rank == 1 else ("row-relegation" if is_rel else ("row-playoff" if is_ply else ""))
                        is_champ = (rank == 1 and (int(df.iloc[0]['points']) - int(df.iloc[1]['points']) > potential or w_left == 0))
                        is_rel_conf = is_rel and ((pts_to_safety - int(row['points']) > potential) or (w_left == 0))
                        clinch_class = "clinch-bold" if is_champ else ""
                        
                        bars = []
                        if is_champ: bars.append("bar-champ")
                        if row['is_cup_winner']: bars.append("bar-gold")
                        if is_rel_conf: bars.append("bar-relegated")
                        inner_bars = "".join([f'<div class="bar {b}"></div>' for b in bars])

                        tri_class = next((s_tri for s_rank, s_tri in slots if s_rank == rank), "")
                        corner_html = f'<div class="corner-left {tri_class}"></div>' if tri_class else ""
                        
                        html += f'<tr class="{row_class} {clinch_class}"><td class="rank-cell">{rank}</td>'
                        html += f'<td class="team-cell">{corner_html}<div class="bar-container">{inner_bars}</div>{row["team_display_name"]}</td>'
                        if show_stats: html += f'<td>{row["wins"]}</td><td>{row["draws"]}</td><td>{row["losses"]}</td>'
                        if show_goals: html += f'<td>{row["gf_sum"]}</td><td>{row["ga_sum"]}</td>'
                        html += f'<td>{row["gp"]}</td><td class="stat-cell-ltr">{row["goal_stat"]}</td><td>{row["points"]}</td>'
                        if show_form: html += f'<td>{get_form_html(row["last_5_detailed"])}</td>'
                        html += '</tr>'
                    return html + '</tbody></table>'

                if int(d['stage_id']) in [11, 12, 13] and uplf > 0:
                    st.markdown('<div class="playoff-label-container">פלייאוף עליון</div>', unsafe_allow_html=True)
                    st.markdown(build_table_only(df.iloc[:uplf], 1, False), unsafe_allow_html=True)
                    offset = uplf
                    if mplf > 0:
                        st.markdown('<div class="playoff-label-container">פלייאוף אמצעי</div>', unsafe_allow_html=True)
                        st.markdown(build_table_only(df.iloc[offset:offset+mplf], offset+1, False), unsafe_allow_html=True)
                        offset += mplf
                    st.markdown('<div class="playoff-label-container">פלייאוף תחתון</div>', unsafe_allow_html=True)
                    st.markdown(build_table_only(df.iloc[offset:], offset+1, True), unsafe_allow_html=True)
                else:
                    st.markdown(build_table_only(df, 1, False), unsafe_allow_html=True)

                deduction_df = df[df['total_deducted'] > 0]
                if not deduction_df.empty:
                    notes = []
                    for _, row in deduction_df.iterrows():
                        pts = int(row['total_deducted'])
                        t_name = row['team_name_raw']
                        if pts == 1: notes.append(f"ל{t_name} הופחתה נקודה")
                        else: notes.append(f"ל{t_name} הופחתו {pts} נקודות")
                    st.markdown(f'<div class="deduction-note">* {", ".join(notes)}</div>', unsafe_allow_html=True)

    except Exception as e: st.error(f"שגיאה: {e}")
