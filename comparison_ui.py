import streamlit as st
import pandas as pd
import os

def show_comparison_ui(client):
    st.subheader("⚖️ השוואת מאזנים: דירוג ואחוזון")

    sql_file_name = "comparison_queries.sql"
    try:
        with open(sql_file_name, "r", encoding='utf-8-sig') as f:
            sql_template = f.read()
    except FileNotFoundError:
        st.error(f"הקובץ {sql_file_name} לא נמצא.")
        return

    def format_smart_decimal(v):
        if pd.isna(v) or v == 0: return "0"
        return f"{int(v)}" if v == int(v) else f"{v:.2f}"

    st.markdown("""
        <style>
        [data-testid="stExpander"] .stVerticalBlock { gap: 0.2rem !important; padding-top: 0.5rem !important; }
        .info-badge { display: flex; gap: 15px; background-color: #f0f4f8; padding: 8px 15px; border-radius: 8px; width: fit-content; margin-bottom: 20px; border: 1px solid #cbd5e1; font-size: 0.9em; }
        div[id^="expander-content"] div[data-testid="stExpander"]:first-of-type label { display: none; }
        </style>
    """, unsafe_allow_html=True)

    plf_map = {"הכל": "הכל", "10": "עונה סדירה", "11": "עליון", "12": "אמצעי", "13": "תחתון"}
    sum_map = {"הכל": "הכל", "champ": "אלופה", "rlg": "יורדת"}
    last_map = {"הכל": "הכל", "rgn": "אלופה מכהנת", "prmt": "עולה חדשה"}
    rev_plf = {v: k for k, v in plf_map.items()}
    rev_sum = {v: k for k, v in sum_map.items()}
    rev_last = {v: k for k, v in last_map.items()}

    @st.cache_data(ttl=3600)
    def get_seasons_and_vitals():
        seasons_df = client.query("select distinct season from `tavla-440015.table.srtdgms` where comp_id = 10 order by season desc").to_dataframe()
        raw_seasons = seasons_df['season'].tolist()
        v_df = client.query("select distinct cast(rk as string) as rk from `tavla-440015.table.tmszn2` where rk is not null").to_dataframe()
        return raw_seasons, v_df

    raw_seasons, v_df = get_seasons_and_vitals()
    season_options = ["כל העונות"] + raw_seasons
    latest_season = max(raw_seasons) if raw_seasons else None

    def reset_filters():
        st.session_state.cs_single = "כל העונות"
        st.session_state.team_sel = "ללא קבוצה"
        st.session_state.week_sel = "מחזור אחרון"
        st.session_state.comp_venue = "כללי"
        st.session_state.sort_col = "success_pct"
        st.session_state.sort_order = "יורד"
        st.session_state.adv_plf = "הכל"
        st.session_state.adv_rk = "הכל"
        st.session_state.adv_sum = "הכל"
        st.session_state.adv_last = "הכל"

    with st.expander("🔍 הגדרות חיפוש ומיון", expanded=True):
        c1 = st.columns([1.2, 0.7, 0.7, 1.8, 1.8])
        with c1[1]:
            s_input = st.selectbox("עונה:", season_options, key='cs_single')
            ref_season = latest_season if s_input == "כל העונות" else s_input
            s_start = min(raw_seasons) if s_input == "כל העונות" else s_input
            s_end = max(raw_seasons) if s_input == "כל העונות" else s_input
        
        teams_df = client.query(f"select distinct t.team from `tavla-440015.table.srtdgms` s join `tavla-440015.table.teams` t on s.team = t.team_id where s.season = {ref_season} and s.comp_id = 10 order by t.team").to_dataframe()
        team_list = ["ללא קבוצה"] + (teams_df['team'].tolist() if not teams_df.empty else [])
        with c1[0]: selected_team_name = st.selectbox("קבוצה:", team_list, key='team_sel')
        with c1[2]:
            target_week_input = st.selectbox("מחזור:", ["מחזור אחרון"] + list(range(1, 39)), key='week_sel')
            sql_week_val = 99 if target_week_input == "מחזור אחרון" else target_week_input
        with c1[3]: venue_type = st.radio("מיקום:", ["כללי", "בית", "חוץ"], horizontal=True, key="comp_venue")

        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        c2 = st.columns([1, 1, 1, 1, 1, 1])
        with c2[0]:
            sort_options = {"success_pct": "% הצלחה", "start_season": "עונה", "wins": "נצחונות", "draws": "תיקו", "losses": "הפסדים", "goal_diff": "הפרש שערים"}
            if target_week_input == "מחזור אחרון": sort_options.update({"gf_per_game": "שערים למשחק", "ga_per_game": "ספיגות למשחק"})
            else: sort_options.update({"goals_for": "זכות", "goals_against": "חובה"})
            sort_by = st.selectbox("מיין לפי:", list(sort_options.keys()), format_func=lambda x: sort_options[x], key="sort_col")
        with c2[1]: sort_order = st.radio("סדר:", ["יורד", "עולה"], horizontal=True, key="sort_order")
        with c2[4]: st.button("🧹 נקה הכל", on_click=reset_filters, use_container_width=True)
        with c2[5]: execute = st.button("🚀 הרץ", type="primary", use_container_width=True)

    with st.expander("📊 פילטרים מתקדמים", expanded=False):
        f_cols = st.columns(4)
        with f_cols[0]: plf_display = st.selectbox("פלייאוף:", list(plf_map.values()), key='adv_plf')
        with f_cols[1]: 
            rk_opts = ["הכל"] + sorted([x for x in v_df['rk'].unique() if pd.notnull(x)], key=int)
            rk_sel = st.selectbox("מיקום סופי:", rk_opts, key='adv_rk')
        with f_cols[2]: sum_display = st.selectbox("סיכום עונה:", list(sum_map.values()), key='adv_sum')
        with f_cols[3]: last_display = st.selectbox("עונה קודמת:", list(last_map.values()), key='adv_last')

    if execute:
        replacement_team = f"'{selected_team_name}'" if selected_team_name != "ללא קבוצה" else "'%'"
        query = sql_template.replace("= @selected_team_name", "like @selected_team_name").replace("@selected_team_name", replacement_team).replace("@season_start", str(s_start)).replace("@season_end", str(s_end)).replace("@target_week", str(sql_week_val)).replace("@venue_filter", f"'{venue_type}'")

        try:
            results_df = client.query(query).to_dataframe()
            if not results_df.empty:
                # סינון מתקדם ב-Python
                if plf_display != "הכל": results_df = results_df[results_df['plf'].astype(str) == rev_plf[plf_display]]
                if rk_sel != "הכל": results_df = results_df[results_df['rk'].astype(str) == rk_sel]
                if sum_display != "הכל": results_df = results_df[results_df['season_sum'].astype(str) == rev_sum[sum_display]]
                if last_display != "הכל": results_df = results_df[results_df['last_season'].astype(str) == rev_last[last_display]]

                if target_week_input == "מחזור אחרון":
                    results_df['gf_per_game'] = results_df['goals_for'] / results_df['games']
                    results_df['ga_per_game'] = results_df['goals_against'] / results_df['games']

                if selected_team_name != "ללא קבוצה":
                    results_df = results_df[results_df['team_name'] == selected_team_name]

                results_df = results_df.sort_values(by=sort_by, ascending=(sort_order == "עולה")).reset_index(drop=True)
                results_df.insert(0, 'rank', results_df.index + 1)
                
                if not results_df.empty:
                    if selected_team_name != "ללא קבוצה":
                        team_data = results_df[results_df['start_season'] == (s_input if s_input != "כל העונות" else latest_season)]
                        if not team_data.empty:
                            curr = team_data.iloc[0]
                            st.markdown(f'<div class="info-badge"><span>מול <b>{int(curr["total_observations"]):,}</b> קבוצות</span><span>|</span><span><b>{int(curr["total_club_seasons"])}</b> עונות</span></div>', unsafe_allow_html=True)
                            cols = st.columns(6)
                            for i, (l, v) in enumerate([("הצלחה", f"{curr['success_pct']}%"), ("נצ'", int(curr['wins'])), ("תיקו", int(curr['draws'])), ("הפס'", int(curr['losses'])), ("זכות", int(curr['goals_for'])), ("חובה", int(curr['goals_against']))]):
                                with cols[i]: st.metric(l, v)
                    st.write("---")

                    def highlight_rows(row):
                        if row['start_season'] == latest_season: return ['background-color: #e0f2fe'] * len(row)
                        elif row.get('status') == 'שיא היסטורי': return ['background-color: #fef3c7'] * len(row)
                        return [''] * len(row)

                    fmts = {'success_pct': "{:.2f}", 'gf_per_game': format_smart_decimal, 'ga_per_game': format_smart_decimal, 'goal_diff': format_smart_decimal}
                    cols_to_show = ['rank', 'start_season', 'team_name', 'games', 'success_pct']
                    if target_week_input == "מחזור אחרון": cols_to_show += ['gf_per_game', 'ga_per_game', 'goal_diff', 'wins', 'draws', 'losses', 'goals_for', 'goals_against']
                    else: cols_to_show += ['wins', 'draws', 'losses', 'goals_for', 'goals_against', 'goal_diff']

                    config = {"rank": "דירוג", "start_season": st.column_config.NumberColumn("עונה", format="%d"), "team_name": "קבוצה", "games": "מש'", "success_pct": "% הצלחה", "gf_per_game": "זכות/מש'", "ga_per_game": "חובה/מש'", "goal_diff": "הפרש", "wins": "נצ'", "draws": "תיקו", "losses": "הפס'", "goals_for": "זכות", "goals_against": "חובה"}
                    
                    final_cols = [c for c in cols_to_show if c in results_df.columns]
                    st.dataframe(results_df[final_cols].style.apply(highlight_rows, axis=1).format(fmts), use_container_width=True, hide_index=True, column_order=final_cols, column_config=config)
            else:
                st.info("לא נמצאו נתונים.")
        except Exception as e:
            st.error(f"שגיאה: {e}")