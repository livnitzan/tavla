import streamlit as st

def show_tpscr_interface(client, sql_template, get_season_data, team_opts, stadium_opts, reset_params, current_team):
    # נתוני עונות
    season_dict = get_season_data()
    season_options = sorted(list(season_dict.keys()), reverse=True)

    st.markdown("### ⚽ פילטרים - טבלת כובשים")
    
    # צמצום מרווחים כללי ב-CSS
    st.markdown("""
        <style>
        .stVerticalBlock {gap: 0.5rem !important;}
        .stHorizontalBlock {gap: 1rem !important;}
        [data-testid="stMetricValue"] {font-size: 1.2rem;}
        </style>
    """, unsafe_allow_html=True)

    # שורה 1: מצב עונה וטווחים (הכל בשורה אחת דחוסה)
    mode = st.radio("מצב עונה:", ["עונה אחת", "טווח עונות", "ללא הגבלה"], horizontal=True, label_visibility="collapsed")
    
    if mode == "עונה אחת":
        c1, c2, c3 = st.columns([1, 2, 5])
        with c1:
            s = st.selectbox("עונה:", season_options, index=0, key='s_single')
            s_start, s_end = s, s
        with c2:
            max_w_actual = int(season_dict.get(s, 100))
            w_start, w_end = st.slider("מחזורים:", 1, max_w_actual, (1, max_w_actual), key='w_slider')

    elif mode == "טווח עונות":
        c1, c2, c3, c4, empty = st.columns([1.2, 0.8, 1.2, 0.8, 2])
        with c1:
            s_start = st.selectbox("מעונה:", season_options, index=min(1, len(season_options)-1), key='s_range_start')
        with c2:
            w_start = st.number_input("ממחזור:", 1, 100, 1, key='w_num_start')
        with c3:
            s_end = st.selectbox("עד עונה:", season_options, index=0, key='s_range_end')
        with c4:
            max_w_end_actual = int(season_dict.get(s_end, 100))
            w_end = st.number_input("עד מחזור:", 1, 100, max_w_end_actual, key='w_num_end')

    else: # מצב "ללא הגבלה"
        s_start, s_end = 1900, 2100
        w_start, w_end = 1, 100

    st.markdown("<hr style='margin: 0.5em 0;'>", unsafe_allow_html=True)

    # שורה 2: מפעלים, קבוצות ויריבות (3 עמודות)
    f1, f2, f3 = st.columns(3)
    with f1:
        sel_comps = st.multiselect("מפעלים:", ["ליגת העל", "גביע המדינה", "אירופה", "נבחרת"], default=["ליגת העל"], key='comp_select')
        comp_map = {"ליגת העל": [10], "גביע המדינה": [11], "אירופה": list(range(20,30)), "נבחרת": list(range(30,100))}
        comp_ids = ",".join(map(str, [idx for c in sel_comps for idx in comp_map[c]])) if sel_comps else "10"
    with f2:
        default_sel_tms = [current_team] if current_team != "ללא" and current_team in team_opts else []
        sel_tms = st.multiselect("קבוצה כובשת:", list(team_opts.keys()), default=default_sel_tms, key='team_select')
        t_filter = "gls.team IN (" + ",".join([str(team_opts[t]) for t in sel_tms]) + ")" if sel_tms else "1=1"
    with f3:
        sel_opps = st.multiselect("יריבה:", list(team_opts.keys()), key='opp_select')
        opp_filter = "gls.rival IN (" + ",".join([str(team_opts[o]) for o in sel_opps]) + ")" if sel_opps else "1=1"

    # שורה 3: מיקום, אצטדיון וצד (3 עמודות)
    f4, f5, f6 = st.columns(3)
    with f4:
        lctn_choice = st.radio("מיקום:", ["הכל", "בית", "חוץ"], horizontal=True, key='lctn_select')
        lctn_map = {"בית": "H", "חוץ": "A"}
        lctn_filter = f"gms.lctn = '{lctn_map[lctn_choice]}'" if lctn_choice != "הכל" else "1=1"
    with f5:
        sel_stads = st.multiselect("אצטדיון:", sorted(list(stadium_opts.keys())), key='stadium_select')
        stadium_filter = "gls.stad_id IN (" + ",".join([str(stadium_opts[s]) for s in sel_stads]) + ")" if sel_stads else "1=1"
    with f6:
        side_choice = st.selectbox("צד באצטדיון:", ["הכל", "צפוני", "דרומי", "מזרחי", "מערבי"], key='side_select')
        side_map = {"צפוני": "n", "דרומי": "s", "מזרחי": "e", "מערבי": "w"}
        side_filter = f"LOWER(gls.side) = '{side_map[side_choice]}'" if side_choice != "הכל" else "1=1"

    # שורה 4: שחקן, כמות תוצאות וצ'קבוקסים
    f7, f8, f9 = st.columns([1.5, 1, 1])
    with f7:
        player_search = st.text_input("חפש שחקן:", "", key='player_search', placeholder="שם שחקן...")
        p_filter = f"gls.scorrer LIKE '%{player_search}%'" if player_search else "1=1"
    with f8:
        limit_choice = st.selectbox("תוצאות:", [20, 50, 100, "ללא הגבלה"], key='limit_select')
        l_str = f"LIMIT {limit_choice}" if limit_choice != "ללא הגבלה" else ""
    with f9:
        # הצמדת הצ'קבוקסים זה לזה
        show_det = "TRUE" if st.checkbox("פירוט קבוצות", key='show_det_cb') else "FALSE"
        own_g = "1=1" if st.checkbox("שערים עצמיים", key='own_g_cb') else "gls.scorrer != 'עצמי'"

    # כפתורים קטנים וצמודים
    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2, empty = st.columns([1, 1, 4])
    with b1: execute = st.button("🚀 הרץ", use_container_width=True)
    with b2: 
        if st.button("🗑️ נקה", use_container_width=True): reset_params()

    if execute:
        try:
            final_sql = sql_template.format(
                season_start=s_start, season_end=s_end, week_start=w_start, week_end=w_end, 
                comp=comp_ids, own_goals_condition=own_g, player_filter=p_filter, team_filter=t_filter, 
                opp_filter=opp_filter, stadium_filter=stadium_filter, side_filter=side_filter, 
                lctn_filter=lctn_filter, show_details_condition=show_det, limit=l_str
            )
            df = client.query(final_sql).to_dataframe()
            if not df.empty:
                display_cols = [c for c in ['שערים', 'קבוצה', 'שחקן'] if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
            else: 
                st.info("לא נמצאו תוצאות.")
        except Exception as e: 
            st.error(f"שגיאה: {e}")