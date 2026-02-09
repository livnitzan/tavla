import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, time, timedelta, datetime

def show_schedule_ui(client, team_opts, stadium_opts, coach_opts):
    st.subheader("🗓️ בדיקת לוח משחקים ומאזנים")

    # --- 1. פונקציות שליפה בסיסיות ---
    @st.cache_data(ttl=3600)
    def get_seasons_and_weeks():
        try:
            df_s = client.query("select distinct season from `tavla-440015.table.srtdgms` where comp_id = 10 order by season desc").to_dataframe()
            seasons = df_s['season'].tolist()
            df_w = client.query("select season, max(week) as max_w from `tavla-440015.table.srtdgms` where comp_id = 10 and done = true group by season").to_dataframe()
            weeks_map = dict(zip(df_w['season'], df_w['max_w']))
            return seasons, weeks_map
        except: return [2026, 2025], {2026: 20, 2025: 36}

    all_seasons, max_weeks_map = get_seasons_and_weeks()
    current_season = all_seasons[0] if all_seasons else None
    plf_map = {"10": "עונה סדירה", "11": "עליון", "12": "אמצעי", "13": "תחתון"}

    # --- 2. לוגיקת חסימה אקטיבית ועדכון אוטומטי ---
    def validate_and_sync():
        s_start = st.session_state.get("sch_s_start")
        s_end = st.session_state.get("sch_s_end")
        if s_end:
            st.session_state["sch_w_end"] = str(max_weeks_map.get(s_end, "1"))
        if s_start and s_end and s_start > s_end:
            st.session_state["sch_s_end"] = s_start
            st.session_state["sch_w_end"] = str(max_weeks_map.get(s_start, "1"))
        if s_start == s_end:
            try:
                w_start = int(st.session_state.sch_w_start) if st.session_state.sch_w_start.isdigit() else 1
                w_end = int(st.session_state.sch_w_end) if st.session_state.sch_w_end.isdigit() else 1
                if w_start > w_end:
                    st.session_state["sch_w_end"] = str(w_start)
            except: pass
        d_from = st.session_state.get("sch_date_from")
        d_to = st.session_state.get("sch_date_to")
        if d_from and d_to and d_from > d_to:
            st.session_state["sch_date_to"] = d_from

    # --- 3. ניהול Session State ---
    if "sch_mode" not in st.session_state:
        st.session_state["sch_mode"] = "ללא הגבלה"

    def set_initial_defaults():
        st.session_state["sch_s_start"] = current_season
        st.session_state["sch_s_end"] = current_season
        st.session_state["sch_w_start"] = "1"
        st.session_state["sch_w_end"] = str(max_weeks_map.get(current_season, "1"))

    if st.session_state.get("needs_reset", False):
        st.session_state["sch_mode"] = "ללא הגבלה"
        set_initial_defaults()
        for k in ["t_teams", "t_coaches", "t_plf", "o_teams", "o_coaches", "o_plf", "sch_venues", "sch_days"]:
            st.session_state[k] = []
        st.session_state["sch_v_type"] = "הכל"
        st.session_state["sch_include_null_time"] = True
        st.session_state["needs_reset"] = False
        st.rerun()

    # --- 4. UI - פאנל פילטרים ---
    with st.expander("🔍 הגדרות חיפוש", expanded=True):
        c1 = st.columns([2, 1, 1])
        with c1[0]:
            mode = st.radio("מצב חיפוש זמן:", ["ללא הגבלה", "טווח עונות ומחזורים", "טווח תאריכים"], horizontal=True, key="sch_mode", on_change=validate_and_sync)
            if mode == "טווח עונות ומחזורים":
                if st.session_state.get("sch_w_start", "") == "": set_initial_defaults()
                ca, cb = st.columns(2)
                with ca:
                    st.selectbox("מעונה:", [None] + all_seasons, index=all_seasons.index(st.session_state.get("sch_s_start", current_season)) + 1 if st.session_state.get("sch_s_start") else 0, format_func=lambda x: "ללא הגבלה" if x is None else str(x), key="sch_s_start", on_change=validate_and_sync)
                    st.text_input("ממחזור:", key="sch_w_start", on_change=validate_and_sync)
                with cb:
                    st.selectbox("עד עונה:", [None] + all_seasons, index=all_seasons.index(st.session_state.get("sch_s_end", current_season)) + 1 if st.session_state.get("sch_s_end") else 0, format_func=lambda x: "ללא הגבלה" if x is None else str(x), key="sch_s_end", on_change=validate_and_sync)
                    st.text_input("עד מחזור:", key="sch_w_end", on_change=validate_and_sync)
            elif mode == "טווח תאריכים":
                da, db = st.columns(2)
                with da: st.date_input("מתאריך:", value=None, key="sch_date_from", on_change=validate_and_sync)
                with db: st.date_input("עד תאריך:", value=None, key="sch_date_to", on_change=validate_and_sync)

        def get_bounds():
            where = "where comp_id = 10"
            if mode == "טווח עונות ומחזורים" and st.session_state.sch_s_start and st.session_state.sch_s_end:
                where += f" and season between {st.session_state.sch_s_start} and {st.session_state.sch_s_end}"
            elif mode == "טווח תאריכים" and st.session_state.sch_date_from and st.session_state.sch_date_to:
                where += f" and date between '{st.session_state.sch_date_from}' and '{st.session_state.sch_date_to}'"
            try:
                sql = f"select distinct team, rival, stad_id, extract(dayofweek from date) as day_id, min(left(cast(time as string), 5)) over() as min_t, max(left(cast(time as string), 5)) over() as max_t from `tavla-440015.table.srtdgms` {where}"
                res = client.query(sql).to_dataframe()
                return set(res['team'])|set(res['rival']), set(res['stad_id']), set(res['day_id']), res['min_t'].iloc[0], res['max_t'].iloc[0]
            except: return set(team_opts.values()), set(stadium_opts.values()), set(range(1,8)), "00:00", "23:59"

        act_t, act_s, act_d, min_t_b, max_t_b = get_bounds()
        f_teams, f_stads = sorted([n for n, tid in team_opts.items() if tid in act_t]), sorted([n for n, sid in stadium_opts.items() if sid in act_s])
        
        f_days = ["שבת", "ראשון", "שני", "סופ\"ש", "לא בסופ\"ש", "שלישי", "רביעי", "חמישי", "שישי"]

        with c1[1]:
            st.selectbox("מיקום:", ["הכל", "בית", "חוץ", "נייטרלי"], key="sch_v_type")
            st.multiselect("אצטדיון:", f_stads, key="sch_venues")
        with c1[2]:
            st.write("**🕒 ימים ושעות**")
            st.multiselect("ימים:", f_days, key="sch_days")
            t_min, t_max = datetime.strptime(min_t_b, "%H:%M").time(), datetime.strptime(max_t_b, "%H:%M").time()
            st.slider("טווח שעות:", min_value=t_min, max_value=t_max, value=(t_min, t_max), format="HH:mm", key="sch_time_range")
            st.checkbox("כלול ללא שעה", value=True, key="sch_include_null_time")

        st.markdown("---")
        t_col, o_col = st.columns(2)
        with t_col:
            st.write("**🔘 הגורם הנבדק**")
            st.multiselect("קבוצות:", f_teams, key="t_teams")
            st.multiselect("מאמנים:", sorted(list(coach_opts.keys())), key="t_coaches")
            st.multiselect("פלייאוף:", list(plf_map.values()), key="t_plf")
        with o_col:
            st.write("**⚔️ היריבה**")
            st.multiselect("קבוצות:", f_teams, key="o_teams")
            st.multiselect("מאמנים:", sorted(list(coach_opts.keys())), key="o_coaches")
            st.multiselect("פלייאוף:", list(plf_map.values()), key="o_plf")
        
        if st.button("🗑️ נקה פילטרים"):
            st.session_state["needs_reset"] = True
            st.rerun()

    # --- 5. בניית שאילתה והרצה ---
    if st.button("🚀 הרץ חיפוש", type="primary", use_container_width=True):
        clauses = ["comp_id = 10", "done = true", "forfeit = false"]
        if not st.session_state.t_teams and not st.session_state.t_coaches: clauses.append("lctn = 'H'")

        if mode == "טווח עונות ומחזורים":
            w_s = int(st.session_state.sch_w_start) if st.session_state.sch_w_start.isdigit() else 1
            w_e = int(st.session_state.sch_w_end) if st.session_state.sch_w_end.isdigit() else 99
            s_s, s_e = st.session_state.sch_s_start, st.session_state.sch_s_end
            if s_s and s_e:
                if s_s == s_e: clauses.append(f"season = {s_s} AND week BETWEEN {w_s} AND {w_e}")
                else: clauses.append(f"((season={s_s} and week>={w_s}) or (season={s_e} and week<={w_e}) or (season>{s_s} and season<{s_e}))")
        elif mode == "טווח תאריכים": clauses.append(f"date BETWEEN '{st.session_state.sch_date_from}' AND '{st.session_state.sch_date_to}'")

        if st.session_state.t_teams: clauses.append(f"team IN ({','.join([str(team_opts[t]) for t in st.session_state.t_teams])})")
        if st.session_state.t_coaches:
            c_vals = ",".join([f"'{coach_opts[x]}'" for x in st.session_state.t_coaches])
            clauses.append(f"tcoach IN ({c_vals})")
        if st.session_state.o_teams: clauses.append(f"rival IN ({','.join([str(team_opts[o]) for o in st.session_state.o_teams])})")
        if st.session_state.o_coaches:
            oc_vals = ",".join([f"'{coach_opts[x]}'" for x in st.session_state.o_coaches])
            clauses.append(f"ocoach IN ({oc_vals})")
        if st.session_state.sch_venues: clauses.append(f"stad_id IN ({','.join([str(stadium_opts[v]) for v in st.session_state.sch_venues])})")
        
        if st.session_state.sch_days:
            day_map = {"שבת": 7, "ראשון": 1, "שני": 2, "שלישי": 3, "רביעי": 4, "חמישי": 5, "שישי": 6}
            selected_codes, special_conditions = [], []
            for d in st.session_state.sch_days:
                if d == "לא בסופ\"ש": special_conditions.append("EXTRACT(DAYOFWEEK FROM date) NOT IN (6, 7)")
                elif d == "סופ\"ש": special_conditions.append("EXTRACT(DAYOFWEEK FROM date) IN (6, 7)")
                else: selected_codes.append(day_map[d])
            day_clauses = []
            if selected_codes: day_clauses.append(f"EXTRACT(DAYOFWEEK FROM date) IN ({','.join(map(str, selected_codes))})")
            if special_conditions: day_clauses.extend(special_conditions)
            if day_clauses: clauses.append(f"({' OR '.join(day_clauses)})")

        t_range = st.session_state.get("sch_time_range")
        if t_range:
            start_t, end_t = t_range[0].strftime("%H:%M"), t_range[1].strftime("%H:%M")
            time_clause = f"LEFT(CAST(game_time AS STRING), 5) BETWEEN '{start_t}' AND '{end_t}'"
            if st.session_state.get("sch_include_null_time"): clauses.append(f"({time_clause} OR game_time IS NULL)")
            else: clauses.append(time_clause)
        
        if st.session_state.t_plf:
            tp_ids = ", ".join([str(k) for k, v in plf_map.items() if v in st.session_state.t_plf])
            clauses.append(f"t_plf IN ({tp_ids})")
        if st.session_state.o_plf:
            op_ids = ", ".join([str(k) for k, v in plf_map.items() if v in st.session_state.o_plf])
            clauses.append(f"o_plf IN ({op_ids})")

        try:
            with open("schedule_queries.sql", "r", encoding='utf-8-sig') as f: base_sql = f.read()
            full_sql = f"SELECT * FROM ({base_sql}) WHERE {' AND '.join(clauses)} ORDER BY date DESC"
            df = client.query(full_sql).to_dataframe()
            
            if not df.empty:
                # --- לוגיקת כותרות HTML ---
                side_a = ", ".join(st.session_state.t_teams + st.session_state.t_coaches)
                side_b = ", ".join(st.session_state.o_teams + st.session_state.o_coaches)
                main_header = side_a if side_a else "כל הקבוצות"
                if side_b: main_header += f" <span style='color: #6b7280; font-weight: normal; margin: 0 10px;'>נגד</span> {side_b}"

                sub_parts = []
                if mode == "טווח עונות ומחזורים":
                    sub_parts.append(f"עונת {st.session_state.sch_s_start} מחזור {st.session_state.sch_w_start} עד עונת {st.session_state.sch_s_end} מחזור {st.session_state.sch_w_end}")
                elif mode == "טווח תאריכים":
                    sub_parts.append(f"תאריכים: {st.session_state.sch_date_from} עד {st.session_state.sch_date_to}")
                
                if st.session_state.sch_v_type != "הכל": sub_parts.append(f"מיקום: {st.session_state.sch_v_type}")
                if st.session_state.sch_venues: sub_parts.append(f"אצטדיון: {', '.join(st.session_state.sch_venues)}")
                
                if st.session_state.sch_days:
                    prefix = "יום בשבוע: " if len(st.session_state.sch_days) == 1 else "ימים בשבוע: "
                    sub_parts.append(f"{prefix}{', '.join(st.session_state.sch_days)}")
                
                if t_range:
                    is_start_min = t_range[0] == t_min
                    is_end_max = t_range[1] == t_max
                    if not (is_start_min and is_end_max):
                        if is_start_min: sub_parts.append(f"לפני {end_t}")
                        elif is_end_max: sub_parts.append(f"אחרי {start_t}")
                        else: sub_parts.append(f"שעות: {start_t}-{end_t}")

                sub_header = " • ".join(sub_parts)

                if st.session_state.t_teams or st.session_state.t_coaches:
                    w, d, l = len(df[df['res'] == 'W']), len(df[df['res'] == 'D']), len(df[df['res'] == 'L'])
                    gf_total, ga_total = df['gf'].sum(), df['ga'].sum()
                    success_rate = ((w * 3 + d) / (len(df) * 3)) * 100 if len(df) > 0 else 0
                    gd = gf_total - ga_total
                    gd_str = f"+{gd}" if gd > 0 else str(gd)

                    st.markdown(f"""
                    <div style="direction: rtl !important; text-align: right !important; font-family: sans-serif; margin-bottom: 20px;">
                        <div style="background-color: #f0f2f6; padding: 18px; border-radius: 12px; border-right: 6px solid #3b82f6; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                            <div style="font-size: 1.25rem; font-weight: bold; color: #111827; margin-bottom: 4px;">{main_header}</div>
                            <div style="font-size: 0.9rem; color: #4b5563; margin-bottom: 20px; font-weight: normal;">{sub_header}</div>
                            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">
                                <div style="background: white; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #e5e7eb;">
                                    <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 4px;">הפרש שערים</div>
                                    <div style="font-size: 1.4rem; font-weight: bold; color: #f59e0b;">({gd_str}) {ga_total}-{gf_total}</div>
                                </div>
                                <div style="background: white; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #e5e7eb;">
                                    <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 4px;">מאזן (ה-ת-נ)</div>
                                    <div style="font-size: 1.4rem; font-weight: bold; color: #10b981;">{l}-{d}-{w}</div>
                                </div>
                                <div style="background: white; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #e5e7eb;">
                                    <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 4px;">אחוזי הצלחה</div>
                                    <div style="font-size: 1.4rem; font-weight: bold; color: #8b5cf6;">{success_rate:.1f}%</div>
                                </div>
                                <div style="background: white; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #e5e7eb;">
                                    <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 4px;">משחקים</div>
                                    <div style="font-size: 1.4rem; font-weight: bold; color: #3b82f6;">{len(df)}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.dataframe(df[['season','week','date', 'home_team','score','away_team','stadium_name','game_time']], use_container_width=True, hide_index=True)
                st.markdown("---")
                with st.expander("🛠️ בדיקת שאילתת SQL (DEBUG)"):
                    st.code(full_sql, language="sql")
            else: st.warning("אין תוצאות.")
        except Exception as e: st.error(f"שגיאה: {e}")