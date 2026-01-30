import streamlit as st

def show_heavy_losses_interface(client, sql_template, team_opts, current_team):
    st.subheader("בונה קריטריונים לניתוח")
    
    # 1. אתחול משתני מצב
    if 'custom_conditions' not in st.session_state:
        st.session_state.custom_conditions = []
    if 'heavy_initialized' not in st.session_state:
        st.session_state.heavy_initialized = False
    if 'heavy_results_df' not in st.session_state:
        st.session_state.heavy_results_df = None
    if 'heavy_summary_text' not in st.session_state:
        st.session_state.heavy_summary_text = None

    # 2. הזרקה חד-פעמית
    if not st.session_state.heavy_initialized:
        if current_team != "ללא" and current_team in team_opts:
            t_id = team_opts[current_team]
            st.session_state.custom_conditions.append({
                "internal_sql": f"gms.team = {t_id}", 
                "txt": f"קבוצה: {current_team}", 
                "is_main_team": True
            })
        st.session_state.heavy_initialized = True
        st.rerun()

    # --- עיצוב CSS לצ'יפים הכחולים ---
    st.markdown("""
        <style>
        div[data-testid="column"] button[kind="secondary"] {
            background-color: #e1effe !important;
            color: #1e429f !important;
            border: 1px solid #a4cafe !important;
            border-radius: 20px !important;
            font-weight: 600 !important;
        }
        div[data-testid="column"] button[kind="primary"] { border-radius: 20px !important; }
        </style>
    """, unsafe_allow_html=True)

    # --- פאנל הוספת קריטריונים ---
    with st.expander("➕ הוסף קריטריון חדש", expanded=True):
        team_names = sorted(list(team_opts.keys()))
        
        st.markdown("**קריטריון סטטיסטי:**")
        c1, c2, c3 = st.columns(3)
        with c1:
            # סדר מעודכן: ספיגה מיד אחרי כיבוש
            stat_options = ["כיבוש (GF)", "ספיגה (GA)", "ניצחונות", "תיקו", "תיקו עם מספר שערים", "הפסדים", "ניצחון בהפרש שערים", "הפסד בהפרש שערים"]
            ctype = st.selectbox("סוג נתון:", stat_options, key="h_stat")
        with c2:
            no_thresh = ctype in ["ניצחונות", "הפסדים", "תיקו"]
            cthresh = st.number_input("רף שערים/הפרש:", 0, 15, 2, disabled=no_thresh, key="h_thresh")
        with c3:
            ctimes = st.number_input("כמה פעמים בעונה?", 1, 38, 1, key="h_times")
        
        if st.button("הוסף סטטיסטיקה", use_container_width=True):
            sql_p, txt_c = "", ""
            if ctype == "תיקו עם מספר שערים": sql_p, txt_c = f"gms.res = 'D' AND gms.gf = {cthresh}", f"תיקו {cthresh}-{cthresh}"
            elif ctype == "כיבוש (GF)": sql_p, txt_c = f"gms.gf >= {cthresh}", f"כיבוש {cthresh}+"
            elif ctype == "ספיגה (GA)": sql_p, txt_c = f"gms.ga >= {cthresh}", f"ספיגה {cthresh}+"
            elif ctype == "ניצחונות": sql_p, txt_c = f"gms.res = 'W'", "ניצחון"
            elif ctype == "תיקו": sql_p, txt_c = f"gms.res = 'D'", "תיקו"
            elif ctype == "הפסדים": sql_p, txt_c = f"gms.res = 'L'", "הפסד"
            elif ctype == "ניצחון בהפרש שערים": sql_p, txt_c = f"gms.gf - gms.ga >= {cthresh}", f"ניצחון {cthresh}+"
            elif ctype == "הפסד בהפרש שערים": sql_p, txt_c = f"gms.ga - gms.gf >= {cthresh}", f"הפסד {cthresh}+"
            
            if sql_p:
                st.session_state.custom_conditions.append({
                    "internal_sql": sql_p, "txt": f"{txt_c} ({ctimes})", 
                    "is_main_team": False, "is_stat": True, "times": ctimes
                })
                st.rerun()

        st.markdown("---")
        c_t1, c_t2 = st.columns(2)
        with c_t1:
            st.markdown("**קבוצה ראשית:**")
            sel_t = st.selectbox("קבוצה:", team_names, index=team_names.index(current_team) if current_team in team_names else 0, key="sel_t_main")
            if st.button("הוסף קבוצה למחקר", use_container_width=True):
                t_id = team_opts[sel_t]
                st.session_state.custom_conditions.append({"internal_sql": f"gms.team = {t_id}", "txt": f"קבוצה: {sel_t}", "is_main_team": True})
                st.rerun()
        with c_t2:
            st.markdown("**יריבה ספציפית:**")
            sel_opp = st.selectbox("יריבה:", team_names, key="sel_opp_main")
            if st.button("הוסף יריבה למחקר", use_container_width=True):
                o_id = team_opts[sel_opp]
                st.session_state.custom_conditions.append({"internal_sql": f"gms.rival = {o_id}", "txt": f"נגד: {sel_opp}", "is_main_team": False, "is_opp": True})
                st.rerun()

    # --- הצגת קריטריונים פעילים (Chips) ---
    if st.session_state.custom_conditions:
        st.write("### קריטריונים פעילים:")
        num_conds = len(st.session_state.custom_conditions)
        cols = st.columns(num_conds + 1)
        for i, cond in enumerate(st.session_state.custom_conditions):
            with cols[i]:
                if st.button(f"{cond['txt']} ✖", key=f"h_chip_{i}", use_container_width=True):
                    st.session_state.custom_conditions.pop(i)
                    st.rerun()
        with cols[-1]:
            if st.button("🗑️ נקה", type="primary", use_container_width=True, key="h_clear_btn"):
                st.session_state.custom_conditions = []
                st.session_state.heavy_results_df = None
                st.rerun()

        st.markdown("---")
        if st.button("🚀 הרץ ניתוח משולב", use_container_width=True, type="primary", key="h_run_main"):
            try:
                # שימוש אחיד ב-internal_sql
                main_teams = [c['internal_sql'] for c in st.session_state.custom_conditions if c.get('is_main_team')]
                opp_teams = [c['internal_sql'] for c in st.session_state.custom_conditions if c.get('is_opp')]
                stat_items = [c for c in st.session_state.custom_conditions if c.get('is_stat')]
                
                having_parts = []
                if main_teams: having_parts.append(f"COUNTIF({' OR '.join(main_teams)}) > 0")
                
                opp_block = f"({' OR '.join(opp_teams)})" if opp_teams else None
                if opp_block and not stat_items: having_parts.append(f"COUNTIF({opp_block}) > 0")

                for s in stat_items:
                    sql_cond = s['internal_sql']
                    if opp_block: sql_cond = f"({sql_cond}) AND {opp_block}"
                    having_parts.append(f"COUNTIF({sql_cond}) >= {s['times']}")

                final_sql = sql_template.format(conditions=" AND ".join(having_parts) if having_parts else "1=1")
                df = client.query(final_sql).to_dataframe()
                st.session_state.heavy_results_df = df
                st.session_state.heavy_summary_text = df['summary_text'].iloc[0] if not df.empty and 'summary_text' in df.columns else None
            except Exception as e:
                st.error(f"שגיאה: {e}")

    # --- הצגת התוצאות ---
    if st.session_state.heavy_results_df is not None:
        df = st.session_state.heavy_results_df
        if not df.empty:
            if st.session_state.heavy_summary_text:
                st.success(st.session_state.heavy_summary_text)
            
            col_r, col_l = st.columns(2, gap="medium")
            with col_r:
                st.subheader("פירוט לפי עונות")
                # יצירת עותק להצגה והוספת עמודה בצד שמאל (סוף הטבלה)
                display_df = df[['עונה', 'קבוצה']].drop_duplicates().copy()
                display_df[''] = 'A'
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            with col_l:
                st.subheader("סיכום הצטברות")
                cols_to_show = [c for c in ['מספר מקרים', 'קבוצות'] if c in df.columns]
                summary_df = df[cols_to_show].drop_duplicates().dropna()
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
        else:
            st.warning("אין תוצאות.")