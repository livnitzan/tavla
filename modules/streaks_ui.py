import streamlit as st
import pandas as pd
from datetime import datetime

def show_streaks_interface(client, sql_template, reset_params):
    st.title("🔥 מנוע חיפוש רצפים")

    st.markdown("""
        <style>
            [data-testid="stPopover"] svg { display: none !important; }
            [data-testid="stPopover"] button {
                border: none !important;
                background: transparent !important;
                padding: 0px !important;
                color: #555 !important;
                font-size: 20px !important;
                box-shadow: none !important;
                width: 100% !important;
                min-height: 30px !important;
            }
            .cell-content { text-align: center; font-size: 16px; white-space: nowrap; width: 100%; font-weight: 500; }
            .header-content { text-align: center; color: #888; font-size: 13px; border-bottom: 1px solid #eee; padding-bottom: 4px; width: 100%; }
            [data-testid="stHorizontalBlock"] { direction: rtl; gap: 0px !important; }
            div[data-testid="stVerticalBlock"] > div { padding-top: 0px !important; padding-bottom: 0px !important; }
            .row-wrap { width: 100%; padding: 8px 0px; border-bottom: 1px solid #f0f0f0; display: block; }
            
            .summary-box {
                background-color: #f8f9fb;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 15px;
                display: flex;
                flex-direction: row; 
                justify-content: space-around;
                border: 1px solid #eef0f2;
                direction: rtl;
            }
            .summary-item { display: flex; flex-direction: column; align-items: center; }
            .summary-label { font-size: 12px; color: #888; margin-bottom: 4px; }
            .summary-value { font-size: 16px; font-weight: bold; color: #222; }
        </style>
    """, unsafe_allow_html=True)

    if "streak_conditions" not in st.session_state:
        st.session_state.streak_conditions = []

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

    def add_condition():
        ctype = st.session_state.temp_ctype
        cop_label = st.session_state.get('temp_cop', 'לפחות')
        cval = st.session_state.get('temp_cval', 1)
        op_map = {"לפחות": ">=", "יותר מ": ">", "בדיוק": "=", "לכל היותר": "<=", "פחות מ": "<"}
        op_sql = op_map.get(cop_label, ">=")
        sql_c, txt_c = "", ""
        if ctype == "כיבוש שערים": sql_c, txt_c = f"m.gf {op_sql} {cval}", f"כיבוש {cop_label} {cval}"
        elif ctype == "ספיגת שערים": sql_c, txt_c = f"m.ga {op_sql} {cval}", f"ספיגה {cop_label} {cval}"
        elif ctype == "הפרש שערים": sql_c, txt_c = f"(m.gf - m.ga) {op_sql} {cval}", f"הפרש {cop_label} {cval}"
        elif ctype == "ניצחון": sql_c, txt_c = "m.res = 'W'", "ניצחון"
        elif ctype == "תיקו": sql_c, txt_c = "m.res = 'D'", "תיקו"
        elif ctype == "הפסד": sql_c, txt_c = "m.res = 'L'", "הפסד"
        elif "ללא" in ctype: 
            target = {'ניצחון': 'W', 'תיקו': 'D', 'הפסד': 'L'}[ctype.replace('ללא ', '')]
            sql_c, txt_c = f"m.res != '{target}'", ctype
        if sql_c: st.session_state.streak_conditions.append({"sql": sql_c, "txt": txt_c})

    teams_df = client.query("SELECT team_id, team FROM `table.teams` WHERE team_id < 100 ORDER BY team").to_dataframe()
    team_options = {row['team']: row['team_id'] for _, row in teams_df.iterrows()}

    with st.expander("🌍 הגדרות מסגרת", expanded=False):
        col_a, col_b = st.columns([2, 1])
        with col_a:
            comps = st.multiselect("מפעלים", options=[10, 11, 1, 2], default=[10], format_func=lambda x: {10: "ליגת העל", 11: "גביע המדינה", 1: "אירופה", 2: "נבחרת"}[x])
        with col_b:
            loc = st.radio("מיקום", ["הכל", "בית", "חוץ"], horizontal=True)
        c_t, c_a = st.columns([3, 1])
        with c_t: selected_teams = st.multiselect("סינון לפי קבוצות (אופציונלי):", options=list(team_options.keys()))
        with c_a: st.write(""); show_active = st.checkbox("פעילים בלבד", value=False)
        st.divider()
        col_s, col_ml, col_lv = st.columns([2, 1, 1])
        with col_s: scope = st.radio("טווח הרצף", ["כל הזמנים", "עונה בודדת", "מתחילת עונה"], horizontal=True)
        with col_ml: min_len = st.number_input("אורך רצף:", value=2, min_value=1)
        with col_lv: limit_val = st.selectbox("הגבלה:", [20, 50, 100, 200, 500], index=1)

    with st.expander("➕ הוסף קריטריון", expanded=True):
        c1, c2, c3 = st.columns([2, 1.5, 1])
        with c1: ctype = st.selectbox("סוג:", ["כיבוש שערים", "ספיגת שערים", "הפרש שערים", "ניצחון", "תיקו", "הפסד", "ללא ניצחון", "ללא תיקו", "ללא הפסד"], key="temp_ctype")
        nv = any(x in ctype for x in ["שערים", "הפרש"])
        with c2: st.selectbox("רף:", ["לפחות", "יותר מ", "בדיוק", "לכל היותר", "פחות מ"], disabled=not nv, key="temp_cop")
        with c3: st.number_input("מספר:", -15 if "הפרש" in ctype else 0, 15, 1, disabled=not nv, key="temp_cval")
        st.button("הוסף", on_click=add_condition)

    if st.session_state.streak_conditions:
        for i, cond in enumerate(st.session_state.streak_conditions):
            cl = st.columns([5, 1])
            cl[0].info(cond["txt"])
            if cl[1].button("🗑️", key=f"d_{i}"): st.session_state.streak_conditions.pop(i); st.rerun()

    if st.button("🚀 הרץ חיפוש", type="primary", use_container_width=True, disabled=not st.session_state.streak_conditions):
        action_sql = " AND ".join([c["sql"] for c in st.session_state.streak_conditions])
        frame_sql = [f"m.comp_id IN ({','.join(map(str, comps))})"]
        if loc != "הכל": frame_sql.append(f"m.lctn = '{'H' if loc == 'בית' else 'A'}'")
        t_f = f"AND m.team IN ({','.join([str(team_options[t]) for t in selected_teams])})" if selected_teams else ""
        a_f = "AND `פעיל` = '✅'" if show_active else ""
        s_p = "season" if scope != "כל הזמנים" else "1"
        query = sql_template.format(frame_conditions=" AND ".join(frame_sql), team_filter=t_f, action_conditions=action_sql, active_only_filter=a_f, scope_partition=s_p, scope_final_filter="").replace("WHERE `רצף` >= 1", f"WHERE `רצף` >= {min_len}").replace("LIMIT 100", f"LIMIT {limit_val}")
        st.session_state.last_results = client.query(query).to_dataframe()

    if "last_results" in st.session_state and st.session_state.last_results is not None:
        res_df = st.session_state.last_results
        st.markdown("---")
        outer_cols = st.columns([0.3, 9.4, 0.3])
        with outer_cols[1]:
            inner_ratios = [0.4, 2.2, 0.7, 1.2, 1.8, 0.4]
            h_cols = st.columns(inner_ratios)
            for col, h in zip(h_cols, ["#", "קבוצה", "רצף", "עונות", "משך", ""]): col.markdown(f"<div class='header-content'>{h}</div>", unsafe_allow_html=True)
            for idx, row in res_df.iterrows():
                with st.container():
                    st.markdown('<div class="row-wrap">', unsafe_allow_html=True)
                    r_cols = st.columns(inner_ratios)
                    r_cols[0].markdown(f"<div class='cell-content'>{idx + 1}</div>", unsafe_allow_html=True)
                    r_cols[1].markdown(f"<div class='cell-content'>{row['קבוצה']}</div>", unsafe_allow_html=True)
                    r_cols[2].markdown(f"<div class='cell-content'><b>{row['רצף']}</b>{' ✅' if row['פעיל'] == '✅' else ''}</div>", unsafe_allow_html=True)
                    r_cols[3].markdown(f"<div class='cell-content'>{row['עונות']}</div>", unsafe_allow_html=True)
                    r_cols[4].markdown(f"<div class='cell-content' style='color:#666;'>{format_duration(row['start_date'], row['end_date'])}</div>", unsafe_allow_html=True)
                    with r_cols[5].popover("⌄"):
                        st.subheader(f"📅 פירוט: {row['קבוצה']}")
                        m_list = row['streak_matches']
                        
                        w = sum(1 for m in m_list if str(m.get('res')).upper() == 'W')
                        d = sum(1 for m in m_list if str(m.get('res')).upper() == 'D')
                        l = sum(1 for m in m_list if str(m.get('res')).upper() == 'L')
                        gf_sum = sum(int(m.get('gf', 0)) for m in m_list)
                        ga_sum = sum(int(m.get('ga', 0)) for m in m_list)

                        st.markdown(f"""
                        <div class="summary-box">
                            <div class="summary-item"><span class="summary-label">משחקים</span><span class="summary-value">{len(m_list)}</span></div>
                            <div class="summary-item"><span class="summary-label">ניצחונות</span><span class="summary-value">{w}</span></div>
                            <div class="summary-item"><span class="summary-label">תיקו</span><span class="summary-value">{d}</span></div>
                            <div class="summary-item"><span class="summary-label">הפסדים</span><span class="summary-value">{l}</span></div>
                            <div class="summary-item"><span class="summary-label">שערים</span><span class="summary-value">{ga_sum}-{gf_sum}</span></div>
                        </div>""", unsafe_allow_html=True)
                        
                        d_html = '<div dir="rtl"><table style="width:100%; border-collapse: collapse; text-align: center; font-size: 13px;">'
                        d_html += '<thead style="background-color: #f1f3f6;"><tr>' + "".join([f'<th style="padding:5px;">{c}</th>' for c in ["#", "תאריך", "עונה", "מחזור", "יריבה", "תוצאה", "📺"]]) + '</tr></thead><tbody>'
                        p, n = row['prev_info'], row['next_info']
                        if p and p.get('prev_rival'): d_html += f'<tr style="background-color: #f8f9fa; color: #888;"><td>—</td><td>{pd.to_datetime(p["prev_date"]).strftime("%d/%m/%Y")}</td><td>{p["prev_season"]}</td><td>{p["prev_week"]}</td><td>{p["prev_rival"]} (לפני)</td><td>{p["prev_ga"]}-{p["prev_gf"]}</td><td><a href="{p["prev_hglts"]}" target="_blank">📺</a></td></tr>'
                        for i, m in enumerate(m_list): d_html += f'<tr style="border-bottom: 1px solid #eee;"><td>{i+1}</td><td>{pd.to_datetime(m["date"]).strftime("%d/%m/%Y")}</td><td>{m["season"]}</td><td>{m["week"]}</td><td>{m["rival_name"]}</td><td>{m["ga"]}-{m["gf"]}</td><td><a href="{m["hglts"]}" target="_blank">📺</a></td></tr>'
                        if n and n.get('next_rival'): d_html += f'<tr style="background-color: #fff5f5; color: #c00;"><td>—</td><td>{pd.to_datetime(n["next_date"]).strftime("%d/%m/%Y")}</td><td>{n["next_season"]}</td><td>{n["next_week"]}</td><td>{n["next_rival"]} (שבירה)</td><td>{n["next_ga"]}-{n["next_gf"]}</td><td><a href="{n["next_hglts"]}" target="_blank">📺</a></td></tr>'
                        st.markdown(d_html + "</tbody></table></div>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🔄 נקה הכל"): st.session_state.streak_conditions = []; st.session_state.last_results = None; reset_params(); st.rerun()