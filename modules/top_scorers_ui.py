import streamlit as st


def show_scorers_interface(client, sql_template, get_season_data, get_filter_options, reset_params):
    # שים לב לשינוי כאן: אנחנו שולחים את ה-client ואת עונה 2024 כברירת מחדל לטעינה הראשונית
    # אם אתה רוצה שהעונה הראשונה תהיה דינמית, נשתמש ב-2024 כ-fallback
    season_dict = get_season_data(client, 2024) 
    
    season_options = sorted(list(season_dict.keys()), reverse=True)
    
    # גם כאן, אנחנו חייבים לשלוח את ה-client כדי שהלוגיקה תדע מאיפה להביא את הקבוצות
    team_opts, stadium_opts = get_filter_options(client)

    st.subheader("פילטרים - טבלת כובשים")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        mode = st.radio("מצב עונה:", ["עונה אחת", "טווח עונות"], horizontal=True, key='mode_choice')
        if mode == "עונה אחת":
            s = st.selectbox("בחר עונה:", season_options, index=0, key='s_single')
            s_start, s_end = s, s
            max_w = int(season_dict.get(s, 36))
            w_start, w_end = st.slider("טווח מחזורים:", 1, max_w, (1, max_w), key='w_slider')
        else:
            sorted_seasons = sorted(list(season_dict.keys()))
            s_start = st.selectbox("מעונה:", sorted_seasons, index=max(0, len(sorted_seasons)-2), key='s_range_start')
            s_end = st.selectbox("עד עונה:", sorted_seasons, index=len(sorted_seasons)-1, key='s_range_end')
            w_start = st.number_input("ממחזור:", 1, 36, 1, key='w_num_start')
            w_end = st.number_input("עד מחזור:", 1, 36, 36, key='w_num_end')

    with c2:
        sel_comps = st.multiselect("מפעלים:", ["ליגת העל", "גביע המדינה", "אירופה", "נבחרת"], default=["ליגת העל"], key='comp_select')
        comp_map = {"ליגת העל": [10], "גביע המדינה": [11], "אירופה": list(range(20,30)), "נבחרת": list(range(30,100))}
        comp_ids = ",".join(map(str, [idx for c in sel_comps for idx in comp_map[c]])) if sel_comps else "10"
        
        # שימוש ב-team_opts שחזר מה-logic
        sel_tms = st.multiselect("קבוצה כובשת:", list(team_opts.keys()), key='team_select')
        t_filter = f"gls.team IN ({','.join([str(team_opts[t]) for t in sel_tms])})" if sel_tms else "1=1"
        
        sel_opps = st.multiselect("יריבה:", list(team_opts.keys()), key='opp_select')
        opp_filter = f"gls.rival IN ({','.join([str(team_opts[o]) for o in sel_opps])})" if sel_opps else "1=1"

    with c3:
        lctn_choice = st.radio("מיקום משחק:", ["הכל", "בית", "חוץ"], horizontal=True, key='lctn_select')
        lctn_map = {"בית": "H", "חוץ": "A"}
        lctn_filter = f"gms.lctn = '{lctn_map[lctn_choice]}'" if lctn_choice != "הכל" else "1=1"
        
        sel_stads = st.multiselect("אצטדיון:", list(stadium_opts.keys()), key='stadium_select')
        stadium_filter = f"gls.stad_id IN ({','.join([str(stadium_opts[s]) for s in sel_stads])})" if sel_stads else "1=1"
        
        side_choice = st.selectbox("צד באצטדיון:", ["הכל", "צפוני", "דרומי", "מזרחי", "מערבי"], key='side_select')
        side_map = {"צפוני": "n", "דרומי": "s", "מזרחי": "e", "מערבי": "w"}
        side_filter = f"LOWER(gls.side) = '{side_map[side_choice]}'" if side_choice != "הכל" else "1=1"

    with c4:
        player_search = st.text_input("חפש שחקן:", "", key='player_search')
        p_filter = f"gls.scorrer LIKE '%{player_search}%'" if player_search else "1=1"
        
        limit_choice = st.selectbox("כמות תוצאות:", [20, 50, 100, "ללא הגבלה"], key='limit_select')
        l_str = f"LIMIT {limit_choice}" if limit_choice != "ללא הגבלה" else ""
        
        show_det = "TRUE" if st.checkbox("הצג פירוט קבוצות", key='show_det_cb') else "FALSE"
        own_g = "1=1" if st.checkbox("כלול שערים עצמיים", key='own_g_cb') else "gls.scorrer != 'עצמי'"

    st.write("---")
    b1, b2 = st.columns(2)
    with b1: 
        execute = st.button("🚀 הרץ שאילתה")
    with b2: 
        if st.button("🗑️ ניקוי פרמטרים"): 
            reset_params()
            st.rerun() # מוודא שהדף מתרענן אחרי הניקוי

    if execute:
        try:
            # שימוש ב-.format() כפי שכתבת במקור
            final_sql = sql_template.format(
                season_start=s_start, season_end=s_end, 
                week_start=w_start, week_end=w_end, 
                comp=comp_ids, own_goals_condition=own_g, 
                player_filter=p_filter, team_filter=t_filter, 
                opp_filter=opp_filter, stadium_filter=stadium_filter, 
                side_filter=side_filter, lctn_filter=lctn_filter, 
                show_details_condition=show_det, limit=l_str
            )
            df = client.query(final_sql).to_dataframe()
            if not df.empty:
                st.subheader("תוצאות")
                display_cols = [c for c in ['שערים', 'קבוצה', 'שחקן'] if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
            else: 
                st.info("לא נמצאו תוצאות.")
        except Exception as e: 
            st.error(f"בעיה בהרצת השאילתה: {e}")
