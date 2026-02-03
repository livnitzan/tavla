import streamlit as st
import pandas as pd
from datetime import datetime

CROWD_UI_STYLE = """
<style>
    .main-rtl-container { direction: rtl; text-align: right; width: 100%; }
    .stVerticalBlock {gap: 0.5rem !important;}
    .stHorizontalBlock {gap: 1rem !important;}
</style>
"""

def show_crowd_interface(client, sql_template, get_season_data, team_opts, stadium_opts, current_team):
    st.markdown(CROWD_UI_STYLE, unsafe_allow_html=True)
    st.markdown('<div class="main-rtl-container">', unsafe_allow_html=True)
    st.markdown("### 🏟️ ניתוח נתוני קהל - ליגת העל")

    tab_research, tab_weeks = st.tabs(["🔍 מחקר חופשי", "📈 סיכום לפי מחזורים"])

    season_dict = get_season_data()
    season_options = sorted([s for s in season_dict.keys() if s >= 2017], reverse=True)

    # --- לשונית 1: מחקר חופשי ---
    with tab_research:
        if 'crowd_filters' not in st.session_state:
            st.session_state['crowd_filters'] = []

        vip_ids = {11: "מכבי תל אביב", 12: "מכבי חיפה", 17: "הפועל באר שבע", 25: "בית\"ר ירושלים", 36: "הפועל תל אביב"}
        special_opts = ["רק גדולות", "רק קטנות"]
        
        with st.expander("🌍 הגדרות חיפוש", expanded=True):
            mode = st.radio("מצב עונה:", ["עונה אחת", "טווח עונות", "ללא הגבלה"], horizontal=True, key="res_mode")
            if mode == "עונה אחת":
                c1, c2, _ = st.columns([1, 2, 5])
                with c1:
                    s_start = st.selectbox("עונה:", season_options, index=0, key='cr_s_single')
                    s_end = s_start
                with c2:
                    max_w_q = f"SELECT MAX(week) as max_w FROM `tavla-440015.table.srtdgms` WHERE season = {s_start} AND tcrowd IS NOT NULL AND comp_id = 10"
                    res_w = client.query(max_w_q).to_dataframe()
                    max_w = int(res_w['max_w'].iloc[0]) if not res_w.empty and pd.notnull(res_w['max_w'].iloc[0]) else 36
                    w_start, w_end = st.slider("מחזורים:", 1, max_w, (1, max_w), key=f'sl_w_{s_start}')
            elif mode == "טווח עונות":
                c1, c2, c3, c4, _ = st.columns([1.2, 0.8, 1.2, 0.8, 2])
                with c1: s_start = st.selectbox("מעונה:", season_options, index=min(1, len(season_options)-1), key='cr_s_r_start')
                with c2: w_start = st.number_input("ממחזור:", 1, 100, 1, key='cr_w_n_start')
                with c3: 
                    allowed_end_seasons = [yr for yr in season_options if yr >= s_start]
                    s_end = st.selectbox("עד עונה:", allowed_end_seasons, index=0, key='cr_s_r_end')
                with c4: 
                    w_end = st.number_input("עד מחזור:", 1, 100, int(season_dict.get(s_end, 36)), key='cr_w_n_end')
            else:
                s_start, s_end, w_start, w_end = 2017, 2100, 1, 100

            st.markdown("---")
            f1, f2, f3, f4 = st.columns([2, 2, 2, 1.5])
            with f1: sel_teams = st.multiselect("קבוצות:", special_opts + sorted(list(team_opts.keys())), default=[current_team] if current_team in team_opts else [], key="ms_teams")
            with f2: sel_rivals = st.multiselect("יריבות:", special_opts + sorted(list(team_opts.keys())), key="ms_rivals")
            with f3: pos_mode = st.radio("מיקום:", ["בית", "חוץ", "הכל"], horizontal=True, key="rb_pos")
            with f4: home_only = st.checkbox("רק אצטדיון ראשי", value=(pos_mode == "בית"), disabled=(pos_mode != "בית"), key="cb_home")

            st.markdown("**🔍 סינון קהל מרובה:**")
            cf1, cf2, cf3, cf4 = st.columns([1.5, 1.5, 1.5, 1])
            with cf1: f_target = st.selectbox("קריטריון:", ["סה\"כ", "בית", "חוץ"], key="f_target_res")
            with cf2: f_op = st.selectbox("תנאי:", ["לפחות", "יותר מ", "בדיוק", "לכל היותר", "פחות מ"], key="f_op_res")
            with cf3: f_val = st.number_input("כמות:", value=0, step=500, key="f_val_res")
            with cf4:
                st.write("") 
                if st.button("➕ הוסף", key="add_filter_btn"):
                    st.session_state['crowd_filters'].append({"target": f_target, "op": f_op, "val": f_val})

            if st.session_state['crowd_filters']:
                cols_tags = st.columns(max(len(st.session_state['crowd_filters']), 1))
                for i, filter_item in enumerate(st.session_state['crowd_filters']):
                    with cols_tags[i]:
                        if st.button(f"❌ {filter_item['target']} {filter_item['op']} {filter_item['val']}", key=f"del_f_{i}"):
                            st.session_state['crowd_filters'].pop(i)
                            st.rerun()
            
            sel_stads = st.multiselect("אצטדיונים:", sorted(list(stadium_opts.keys())), key="ms_stads")

        st.markdown(" ") 
        b1, b2, b3, b4, b5 = st.columns([0.7, 0.7, 1.1, 1.3, 1.3])
        with b1: execute = st.button("🚀 הרץ מחקר", type="primary", key="exec_res")
        with b2: 
            if st.button("🗑️ נקה", key="clear_res"):
                st.session_state['crowd_results'] = None
                st.session_state['crowd_filters'] = []
                st.rerun()
        with b3: limit_choice = st.selectbox("תוצאות:", [20, 50, 100, "ללא הגבלה"], index=1, label_visibility="collapsed", key="lim_res")
        with b4: sort_by_choice = st.selectbox("מיין לפי:", ["תאריך", "קהל"], index=0, label_visibility="collapsed", key="sort_res")
        with b5: sort_order_choice = st.radio("סדר:", ["יורד", "עולה"], horizontal=True, label_visibility="collapsed", key="order_res")

        if execute:
            try:
                query_ready = sql_template.replace("m.season BETWEEN {season_start} AND {season_end}", "1=1").replace("m.week BETWEEN {week_start} AND {week_end}", f"(m.season * 100 + m.week) >= ({s_start} * 100 + {w_start}) AND (m.season * 100 + m.week) <= ({s_end} * 100 + {w_end})")
                df = client.query(query_ready).to_dataframe()
                df.columns = [c.lower() for c in df.columns]

                def apply_team_filter(dataframe, selected, col_id, col_name):
                    if not selected: return dataframe
                    mask = pd.Series(False, index=dataframe.index)
                    if "רק גדולות" in selected: mask |= dataframe[col_id].isin(vip_ids.keys())
                    if "רק קטנות" in selected: mask |= ~dataframe[col_id].isin(vip_ids.keys())
                    specs = [x for x in selected if x not in special_opts]
                    if specs: mask |= dataframe[col_name].isin(specs)
                    return dataframe[mask]

                if pos_mode == "בית": 
                    df = apply_team_filter(df, sel_teams, 'team_id', 'team_name')
                    df = apply_team_filter(df, sel_rivals, 'rival_id', 'rival_name')
                elif pos_mode == "חוץ": 
                    df = apply_team_filter(df, sel_teams, 'rival_id', 'rival_name')
                    df = apply_team_filter(df, sel_rivals, 'team_id', 'team_name')
                else: 
                    df_h = apply_team_filter(df.copy(), sel_teams + sel_rivals, 'team_id', 'team_name')
                    df_a = apply_team_filter(df.copy(), sel_teams + sel_rivals, 'rival_id', 'rival_name')
                    df = pd.concat([df_h, df_a]).drop_duplicates(subset=['game_id'])

                if sel_stads: df = df[df['stadium'].isin(sel_stads)]
                df['calc_total'] = df['tcrowd'].fillna(0) + df['rcrowd'].fillna(0)
                for f_item in st.session_state['crowd_filters']:
                    col = 'tcrowd' if f_item['target'] == "בית" else ('rcrowd' if f_item['target'] == "חוץ" else 'calc_total')
                    if f_item['op'] == "לפחות": df = df[df[col] >= f_item['val']]
                    elif f_item['op'] == "יותר מ": df = df[df[col] > f_item['val']]
                    elif f_item['op'] == "בדיוק": df = df[df[col] == f_item['val']]
                    elif f_item['op'] == "לכל היותר": df = df[df[col] <= f_item['val']]
                    elif f_item['op'] == "פחות מ": df = df[df[col] < f_item['val']]

                st.session_state['crowd_results'] = {'full_data': df, 'pos_mode': pos_mode, 'limit': limit_choice, 'sort_by': sort_by_choice, 'sort_order': sort_order_choice}
            except Exception as e: st.error(f"שגיאה: {e}")

        if st.session_state.get('crowd_results'):
            res = st.session_state['crowd_results']
            full_df = res['full_data']
            if not full_df.empty:
                is_asc = (res.get('sort_order') == "עולה")
                if res.get('sort_by') == "תאריך": 
                    full_df['date'] = pd.to_datetime(full_df['date'])
                    df_sorted = full_df.sort_values('date', ascending=is_asc)
                else: 
                    crowd_col_sort = 'tcrowd' if res['pos_mode'] != "חוץ" else 'rcrowd'
                    df_sorted = full_df.sort_values(crowd_col_sort, ascending=is_asc)
                
                st.subheader("📋 סיכום נתונים")
                team_col = 'team_name' if res['pos_mode'] != "חוץ" else 'rival_name'
                crowd_sum_col = 'tcrowd' if res['pos_mode'] != "חוץ" else 'rcrowd'
                summary = df_sorted.groupby(['season', team_col]).agg({crowd_sum_col: ['mean', 'count']}).reset_index()
                summary.columns = ['עונה', 'קבוצה', 'ממוצע', 'משחקים']
                summary['ממוצע'] = summary['ממוצע'].round(0).astype(int)
                st.dataframe(summary.sort_values('ממוצע', ascending=False), use_container_width=True, hide_index=True)

                st.subheader("🏟️ פירוט משחקים")
                final_limit = res['limit']
                final_df = df_sorted.head(int(final_limit)) if final_limit != "ללא הגבלה" else df_sorted
                final_df['תוצאה'] = final_df['gf'].fillna(0).astype(int).astype(str) + "-" + final_df['ga'].fillna(0).astype(int).astype(str)
                final_df['סה"כ'] = final_df['tcrowd'].fillna(0) + final_df['rcrowd'].fillna(0)
                st.dataframe(final_df[['season', 'week', 'team_name', 'rival_name', 'stadium', 'תוצאה', 'סה"כ', 'tcrowd', 'rcrowd']].rename(columns={'season': 'עונה', 'week': 'מחזור', 'team_name': 'בית', 'rival_name': 'חוץ', 'stadium': 'אצטדיון', 'tcrowd': 'קהל בית', 'rcrowd': 'קהל חוץ'}), use_container_width=True, hide_index=True)


# --- לשונית 2: סיכום לפי מחזורים ---
    with tab_weeks:
        st.markdown("""
            <style>
                .crowd-table { 
                    width: 100%; 
                    border-collapse: collapse; 
                    direction: rtl; 
                    font-family: sans-serif; 
                    table-layout: fixed; 
                }
                .crowd-header-cell { 
                    padding: 8px 2px; 
                    text-align: center; 
                    font-size: 13px; 
                    color: #444; 
                    font-weight: 600; 
                    background-color: #f8f9fa;
                    border-bottom: 2px solid #dee2e6;
                }
                .main-round-row {
                    background-color: #e1effe !important;
                    border-bottom: 1px solid #b2d7ff;
                    transition: background-color 0.2s;
                }
                .main-round-row:hover {
                    background-color: #cce3ff !important;
                }
                .crowd-cell { 
                    padding: 10px 2px; 
                    text-align: center; 
                    font-size: 15px; 
                    color: #1e429f;
                }
                .crowd-bold { font-weight: bold; }
                .details-table { width: 100%; background-color: white; border-collapse: collapse; }
                .details-cell { padding: 6px; border-bottom: 1px solid #eee; text-align: center; font-size: 12px; color: #333; }
                .stExpander { border: none !important; box-shadow: none !important; }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("<h4 style='text-align: center;'>📊 ניתוח קהל ברמת מחזור</h4>", unsafe_allow_html=True)
        
        with st.expander("🌍 הגדרות בחירה", expanded=True):
            w_mode = st.radio("מצב עונה:", ["עונה אחת", "טווח עונות", "ללא הגבלה"], horizontal=True, key="weeks_mode")
            if w_mode == "עונה אחת":
                c1, _ = st.columns([1, 4])
                with c1: ws_start = st.selectbox("עונה:", season_options, index=0, key='ws_single'); ws_end = ws_start
            elif w_mode == "טווח עונות":
                c1, c2, _ = st.columns([1, 1, 3])
                with c1: ws_start = st.selectbox("מעונה:", season_options, index=min(1, len(season_options)-1), key='ws_range_start')
                with c2: 
                    allowed_end = [yr for yr in season_options if yr >= ws_start]
                    ws_end = st.selectbox("עד עונה:", allowed_end, index=0, key='ws_range_end')
            else:
                ws_start, ws_end = 2017, 2100

        _, btn_col, _ = st.columns([1.5, 1, 1.5])
        with btn_col:
            run_query = st.button("🚀 הרץ ניתוח", type="primary", use_container_width=True, key="ws_btn")

        if run_query or st.session_state.get('df_weeks_current') is not None:
            if run_query:
                query_weeks = f"""
                    SELECT 
                        m.season, m.week, 
                        SUM(m.tcrowd + COALESCE(m.rcrowd, 0)) as total_cr,
                        ARRAY_AGG(STRUCT(
                            t1.team as home_team, 
                            t2.team as away_team,
                            st.stadium as stadium_name,
                            (m.tcrowd + COALESCE(m.rcrowd, 0)) as total_match_crowd
                        ) ORDER BY (m.tcrowd + COALESCE(m.rcrowd, 0)) DESC) as matches
                    FROM `tavla-440015.table.srtdgms` m
                    LEFT JOIN `tavla-440015.table.teams` t1 ON m.team = t1.team_id
                    LEFT JOIN `tavla-440015.table.teams` t2 ON m.rival = t2.team_id
                    LEFT JOIN `tavla-440015.table.stads` st ON m.stad_id = st.stad_id
                    WHERE m.tcrowd IS NOT NULL AND m.lctn = 'H' AND m.comp_id = 10
                      AND m.season BETWEEN {ws_start} AND {ws_end}
                    GROUP BY m.season, m.week ORDER BY total_cr DESC
                """
                df_res = client.query(query_weeks).to_dataframe()
                st.session_state['df_weeks_current'] = df_res if not df_res.empty else None
                st.session_state['weeks_show_all'] = False

            if st.session_state.get('df_weeks_current') is not None:
                df_comp = st.session_state['df_weeks_current']
                
                # מכולה מרכזית צרה (1:2:1)
                _, mid_area, _ = st.columns([1, 2, 1])
                
                with mid_area:
                    with st.expander("🔍 בדיקת מיקום יחסי", expanded=False):
                        chk_s = st.selectbox("עונה:", sorted(df_comp['season'].unique(), reverse=True), key="chk_s")
                        chk_w = st.selectbox("מחזור:", sorted(df_comp[df_comp['season'] == chk_s]['week'].unique()), key="chk_w")
                        if st.button("📊 בדוק", use_container_width=True):
                            match = df_comp[(df_comp['season'] == chk_s) & (df_comp['week'] == chk_w)]
                            if not match.empty:
                                val = int(match['total_cr'].iloc[0])
                                rank = df_comp[df_comp['total_cr'] >= val].shape[0]
                                st.info(f"מקום {rank} ({val:,} צופים)")

                    st.markdown("---")
                    st.markdown("""<table class="crowd-table"><thead><tr><th style="width: 25%;">עונה</th><th style="width: 20%;">מחזור</th><th style="width: 55%;">סה"כ קהל</th></tr></thead></table>""", unsafe_allow_html=True)

                    show_all = st.session_state.get('weeks_show_all', False)
                    
                    def render_rows(data):
                        for _, row in data.iterrows():
                            st.markdown(f"""
                                <table class="crowd-table">
                                    <tr class="main-round-row">
                                        <td class="crowd-cell" style="width: 25%;">{int(row['season'])}</td>
                                        <td class="crowd-cell" style="width: 20%;">{int(row['week'])}</td>
                                        <td class="crowd-cell crowd-bold" style="width: 55%;">{int(row['total_cr']):,}</td>
                                    </tr>
                                </table>
                            """, unsafe_allow_html=True)
                            with st.expander("🔍 פירוט"):
                                # סדר עמודות: קהל (25%), אצטדיון (35%), משחק (40%)
                                inner = '<table class="details-table"><thead><tr style="background:#f9f9f9;"><th class="details-cell" style="width:25%;">קהל</th><th class="details-cell" style="width:35%;">אצטדיון</th><th class="details-cell" style="width:40%;">משחק</th></tr></thead><tbody>'
                                for m in row['matches']:
                                    s_display = m.get('stadium_name') if m.get('stadium_name') else "---"
                                    inner += f"<tr><td class='details-cell' style='font-weight:bold;'>{int(m['total_match_crowd']):,}</td><td class='details-cell' style='color:#666;'>{s_display}</td><td class='details-cell'>{m['home_team']} - {m['away_team']}</td></tr>"
                                st.markdown(inner + "</tbody></table>", unsafe_allow_html=True)

                    render_rows(df_comp.head(5))

                    if len(df_comp) > 5:
                        if not show_all:
                            if st.button(f"👇 הצג עוד {len(df_comp)-5}", use_container_width=True):
                                st.session_state['weeks_show_all'] = True
                                st.rerun()
                        else:
                            if st.button("👆 הצג טופ 5 בלבד", use_container_width=True):
                                st.session_state['weeks_show_all'] = False
                                st.rerun()
                            render_rows(df_comp.iloc[5:])