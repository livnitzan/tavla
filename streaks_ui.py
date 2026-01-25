import streamlit as st
import pandas as pd
from datetime import datetime

def show_streaks_interface(client, sql_template, team_opts, reset_params, current_team, stadium_opts):
    # שימוש בסוגריים כפולים {{ }} ב-CSS כדי למנוע KeyError בזמן format של ה-SQL
    st.markdown(f"""
        <style>
            .main-rtl-container {{
                direction: rtl;
                text-align: right;
                width: 100%;
            }}

            @media (min-width: 1024px) {{
                .main-rtl-container {{ 
                    max-width: 650px; 
                    margin: 0 auto; 
                }}
            }}

            .custom-streak-row {{
                display: flex;
                align-items: center;
                gap: 12px; 
                padding: 12px 0;
                border-bottom: 1px solid #f0f0f0;
                direction: rtl;
                justify-content: flex-start;
            }}

            .badge-area {{
                min-width: 45px;
                text-align: center;
                background-color: #f0f7ff;
                color: #007bff;
                border-radius: 8px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 16px;
                flex-shrink: 0;
            }}

            .info-area {{
                display: flex;
                flex-direction: column;
                text-align: right;
            }}

            .team-name-text {{
                font-size: 16px;
                font-weight: bold;
                color: #222;
                line-height: 1.2;
            }}

            .meta-text {{
                font-size: 12px;
                color: #888;
            }}

            [data-testid="stPopover"] svg {{ display: none !important; }}
            [data-testid="stPopover"] button {{
                border: 1px solid #d1e5ff !important;
                background-color: #f0f7ff !important;
                color: #007bff !important;
                border-radius: 50% !important;
                width: 32px !important;
                height: 32px !important;
                min-height: 32px !important;
                padding: 0px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                margin-top: -5px !important;
            }}

            .summary-box {{
                background-color: #f8f9fb; border-radius: 8px; padding: 12px;
                margin-bottom: 15px; display: flex; flex-direction: row; 
                justify-content: space-around; border: 1px solid #eef0f2; direction: rtl;
            }}
            .summary-item {{ display: flex; flex-direction: column; align-items: center; }}
            .summary-label {{ font-size: 12px; color: #888; margin-bottom: 4px; }}
            .summary-value {{ font-size: 16px; font-weight: bold; color: #222; }}
            
            div[data-testid="column"] button[kind="secondary"] {{
                background-color: #e1effe !important;
                color: #1e429f !important;
                border: 1px solid #a4cafe !important;
                border-radius: 20px !important;
                font-weight: 600 !important;
            }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-rtl-container">', unsafe_allow_html=True)
    st.markdown("### 📈 ניתוח רצפים")

    def format_duration(start_date, end_date):
        diff = pd.to_datetime(end_date) - pd.to_datetime(start_date)
        days = diff.days
        if days < 0: return "0 ימים"
        y, r = divmod(days, 365)
        m, r = divmod(r, 30)
        parts = []
        if y > 0: parts.append(f"{y} שנ'")
        if m > 0: parts.append(f"{m} חו'")
        if not y and not m: parts.append(f"{days} ימים")
        return " ".join(parts) if parts else "יום אחד"

    if "streak_conditions" not in st.session_state:
        st.session_state.streak_conditions = []

    with st.expander("🌍 הגדרות מסגרת", expanded=True):
        e1, e2, e3 = st.columns([1, 1.5, 1])
        with e1:
            sel_comps = st.multiselect("מפעלים:", ["ליגת העל", "גביע המדינה", "אירופה"], default=["ליגת העל"], key='strk_comps')
            comp_map = {"ליגת העל": [10], "גביע המדינה": [11], "אירופה": list(range(20,30))}
            comp_ids = [idx for c in sel_comps for idx in comp_map[c]] if sel_comps else [10]
            frame_cond = f"m.comp_id IN ({','.join(map(str, comp_ids))})"
        with e2:
            lctn_choice = st.radio("מיקום:", ["הכל", "בית", "חוץ"], horizontal=True, key='strk_lctn')
            lctn_map = {"בית": " AND m.lctn = 'H'", "חוץ": " AND m.lctn = 'A'"}
            frame_cond += lctn_map.get(lctn_choice, "")
        with e3:
            active_only = st.checkbox("פעילים בלבד", value=False, key='strk_active')
            active_filter = "AND `פעיל` = '✅'" if active_only else ""

        st.markdown("---")
        c_t1, c_t2, c_t3 = st.columns([1.5, 1.5, 2])
        with c_t1:
            default_tms = [current_team] if current_team != "ללא" and current_team in team_opts else []
            sel_tms = st.multiselect("סינון לפי קבוצות:", list(team_opts.keys()), default=default_tms, key='strk_teams')
            t_filter = "AND m.team IN (" + ",".join([str(team_opts[t]) for t in sel_tms]) + ")" if sel_tms else ""
        with c_t2:
            sel_opps = st.multiselect("סינון לפי יריבות:", list(team_opts.keys()), key='strk_opps')
            frame_cond += " AND m.rival IN (" + ",".join([str(team_opts[o]) for o in sel_opps]) + ")" if sel_opps else ""
        with c_t3:
            sel_stads = st.multiselect("אצטדיון:", sorted(list(stadium_opts.keys())), key='stadium_select')
            frame_cond += " AND m.stad_id IN (" + ",".join([str(stadium_opts[s]) for s in sel_stads]) + ")" if sel_stads else ""

    with st.expander("⏳ הגדרות טווח הרצף", expanded=True):
        t1, t2, t3 = st.columns([1.5, 1.5, 1])
        with t1:
            scope = st.radio("טווח הרצף", ["כל הזמנים", "עונה בודדת", "מתחילת עונה"], horizontal=True, key='strk_scope')
        with t2:
            min_len = st.number_input("אורך רצף לפחות:", 1, 50, 2, key='strk_min_len')
        with t3:
            limit_val = st.selectbox("הגבלה:", [20, 50, 100, 200, 500], index=1, key='strk_limit')

    with st.expander("➕ הוסף קריטריון", expanded=True):
        c1, c2, c3 = st.columns([2, 1.5, 1])
        with c1: ctype = st.selectbox("סוג:", ["כיבוש שערים", "ספיגת שערים", "הפרש שערים", "ניצחון", "תיקו", "הפסד", "ללא ניצחון", "ללא תיקו", "ללא הפסד"], key="temp_ctype")
        nv = any(x in ctype for x in ["שערים", "הפרש"])
        with c2: cop = st.selectbox("רף:", ["לפחות", "יותר מ", "בדיוק", "לכל היותר", "פחות מ"], disabled=not nv, key="temp_cop")
        with c3: cval = st.number_input("מספר:", -15 if "הפרש" in ctype else 0, 15, 1, disabled=not nv, key="temp_cval")
        if st.button("הוסף", use_container_width=True):
            op_map = {"לפחות": ">=", "יותר מ": ">", "בדיוק": "=", "לכל היותר": "<=", "פחות מ": "<"}
            if nv:
                col = "m.gf" if "כיבוש" in ctype else "m.ga" if "ספיגה" in ctype else "(m.gf - m.ga)"
                sql, txt = f"{col} {op_map.get(cop, '>=')} {cval}", f"{ctype} {cop} {cval}"
            else:
                res_map = {"ניצחון": "m.res = 'W'", "תיקו": "m.res = 'D'", "הפסד": "m.res = 'L'", "ללא ניצחון": "m.res != 'W'", "ללא תיקו": "m.res != 'D'", "ללא הפסד": "m.res != 'L'"}
                sql, txt = res_map[ctype], ctype
            st.session_state.streak_conditions.append({"sql": sql, "txt": txt}); st.rerun()

    if st.session_state.streak_conditions:
        cols = st.columns(len(st.session_state.streak_conditions) + 1)
        for i, cond in enumerate(st.session_state.streak_conditions):
            with cols[i]:
                if st.button(f"{cond['txt']} ✖", key=f"s_chip_{i}", use_container_width=True):
                    st.session_state.streak_conditions.pop(i); st.rerun()

    st.markdown("---")
    if st.button("🚀 הרץ חיפוש", use_container_width=True, type="primary"):
        action_sql = " AND ".join([c["sql"] for c in st.session_state.streak_conditions]) if st.session_state.streak_conditions else "1=1"
        now = datetime.now()
        current_season = now.year if now.month >= 7 else now.year - 1
        s_p = "season" if scope != "כל הזמנים" else "1"
        
        s_f_f = ""
        if scope == "מתחילת עונה":
            s_f_f = f"AND streak_start_row = first_game_row_in_season" if scope == "מתחילת עונה" else ""
        
        query = sql_template.format(
            action_conditions=action_sql, frame_conditions=frame_cond, team_filter=t_filter,
            scope_partition=s_p, active_only_filter=active_filter, scope_final_filter=s_f_f
        ).replace("WHERE `רצף` >= 1", f"WHERE `רצף` >= {min_len}").replace("LIMIT 100", f"LIMIT {limit_val}")
        st.session_state.last_streak_results = client.query(query).to_dataframe()

    if "last_streak_results" in st.session_state and st.session_state.last_streak_results is not None:
        for idx, row in st.session_state.last_streak_results.iterrows():
            with st.container():
                c_main, c_btn = st.columns([0.9, 0.1])
                with c_main:
                    st.markdown(f'<div class="custom-streak-row"><div class="badge-area">{row["רצף"]}</div><div class="info-area"><div class="team-name-text">{row["קבוצה"]}{" ✅" if row["פעיל"] == "✅" else ""}</div><div class="meta-text">{row["עונות"]} • {format_duration(row["start_date"], row["end_date"])}</div></div></div>', unsafe_allow_html=True)
                with c_btn:
                    with st.popover("⌄"):
                        m_list = row['streak_matches']
                        w, d, l = sum(1 for m in m_list if str(m.get('res')).upper() == 'W'), sum(1 for m in m_list if str(m.get('res')).upper() == 'D'), sum(1 for m in m_list if str(m.get('res')).upper() == 'L')
                        gf_sum, ga_sum = sum(int(m.get('gf', 0)) for m in m_list), sum(int(m.get('ga', 0)) for m in m_list)
                        
                        st.markdown(f"""<div class="summary-box">
                            <div class="summary-item"><span class="summary-label">משחקים</span><span class="summary-value">{len(m_list)}</span></div>
                            <div class="summary-item"><span class="summary-label">נצ"</span><span class="summary-value">{w}</span></div>
                            <div class="summary-item"><span class="summary-label">תיקו</span><span class="summary-value">{d}</span></div>
                            <div class="summary-item"><span class="summary-label">שערים</span><span class="summary-value">{ga_sum}-{gf_sum}</span></div>
                        </div>""", unsafe_allow_html=True)
                        
                        d_html = '<div dir="rtl"><table style="width:100%; border-collapse: collapse; text-align: center; font-size: 13px;">'
                        d_html += '<thead style="background-color: #f1f3f6;"><tr><th>#</th><th>תאריך</th><th>עונה</th><th>מחזור</th><th>יריבה</th><th>תוצאה</th><th>📺</th></tr></thead><tbody>'
                        
                        p, n = row.get('prev_info', {}), row.get('next_info', {})
                        if scope != "מתחילת עונה" and p and p.get('prev_rival'):
                            d_html += f'<tr style="background-color: #f8f9fa; color: #888;"><td>—</td><td>{pd.to_datetime(p["prev_date"]).strftime("%d/%m/%Y")}</td><td>{p["prev_season"]}</td><td>{p["prev_week"]}</td><td>{p["prev_rival"]} (לפני)</td><td>{p["prev_ga"]}-{p["prev_gf"]}</td><td><a href="{p.get("prev_hglts", "")}" target="_blank">📺</a></td></tr>'
                        
                        for i, m in enumerate(m_list):
                            d_html += f'<tr style="border-bottom: 1px solid #eee;"><td>{i+1}</td><td>{pd.to_datetime(m["date"]).strftime("%d/%m/%Y")}</td><td>{m["season"]}</td><td>{m["week"]}</td><td>{m["rival_name"]}</td><td>{m["ga"]}-{m["gf"]}</td><td><a href="{m.get("hglts", "")}" target="_blank">📺</a></td></tr>'
                        
                        if n and n.get('next_rival'):
                            d_html += f'<tr style="background-color: #fff5f5; color: #c00;"><td>—</td><td>{pd.to_datetime(n["next_date"]).strftime("%d/%m/%Y")}</td><td>{n["next_season"]}</td><td>{n["next_week"]}</td><td>{n["next_rival"]} (שבירה)</td><td>{n["next_ga"]}-{n["next_gf"]}</td><td><a href="{n.get("next_hglts", "")}" target="_blank">📺</a></td></tr>'
                        st.markdown(d_html + "</tbody></table></div>", unsafe_allow_html=True)

    if st.button("🔄 איפוס"):
        st.session_state.streak_conditions = []; st.session_state.last_streak_results = None; reset_params(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)