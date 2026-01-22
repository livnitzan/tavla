import streamlit as st

def show_heavy_losses_interface(client, sql_template):
    st.subheader("בונה קריטריונים לניתוח")
    
    # אתחול רשימת התנאים בתוך הפונקציה אם לא קיימת
    if 'custom_conditions' not in st.session_state:
        st.session_state.custom_conditions = []
    
    with st.expander("➕ הוסף קריטריון חדש", expanded=True):
        # סדר: סוג (ימין) -> רף (אמצע) -> פעמים (שמאל)
        c1, c2, c3 = st.columns(3)
        with c1:
            ctype = st.selectbox("סוג נתון:", ["ספיגה (GA)", "כיבוש (GF)", "ניצחונות", "הפסדים", "ניצחון בהפרש שערים", "הפסד בהפרש שערים"])
        with c2:
            no_thresh = ctype in ["ניצחונות", "הפסדים"]
            cthresh = st.number_input("רף (שערים / הפרש):", 0, 15, 4, disabled=no_thresh)
        with c3:
            ctimes = st.number_input("כמה פעמים בעונה?", 1, 38, 1)
        
        if st.button("הוסף לרשימת התנאים"):
            if "ניצחונות" in ctype: 
                sql_c, txt_c = f"COUNTIF(gms.res = 'W') >= {ctimes}", f"לפחות {ctimes} ניצחונות"
            elif "הפסדים" in ctype: 
                sql_c, txt_c = f"COUNTIF(gms.res = 'L') >= {ctimes}", f"לפחות {ctimes} הפסדים"
            elif "כיבוש" in ctype: 
                sql_c, txt_c = f"COUNTIF(gms.gf >= {cthresh}) >= {ctimes}", f"כיבוש {cthresh}+ שערים לפחות {ctimes} פעמים"
            elif "ספיגה" in ctype: 
                sql_c, txt_c = f"COUNTIF(gms.ga >= {cthresh}) >= {ctimes}", f"ספיגה {cthresh}+ שערים לפחות {ctimes} פעמים"
            elif "ניצחון בהפרש" in ctype:
                sql_c, txt_c = f"COUNTIF(gms.gf - gms.ga >= {cthresh}) >= {ctimes}", f"ניצחון בהפרש {cthresh}+ לפחות {ctimes} פעמים"
            elif "הפסד בהפרש" in ctype:
                sql_c, txt_c = f"COUNTIF(gms.ga - gms.gf >= {cthresh}) >= {ctimes}", f"הפסד בהפרש {cthresh}+ לפחות {ctimes} פעמים"
            
            st.session_state.custom_conditions.append({"sql": sql_c, "txt": txt_c})
            st.rerun()

    if st.session_state.custom_conditions:
        st.write("### קריטריונים פעילים (שילוב של כולם):")
        for i, cond in enumerate(st.session_state.custom_conditions):
            col_txt, col_btn = st.columns([0.9, 0.1])
            col_txt.info(f"🔹 {cond['txt']}")
            if col_btn.button("🗑️", key=f"del_{i}"):
                st.session_state.custom_conditions.pop(i)
                st.rerun()

        if st.button("🚀 הרץ ניתוח משולב"):
            try:
                all_sql_conds = " AND ".join([c['sql'] for c in st.session_state.custom_conditions])
                final_sql = sql_template.format(conditions=all_sql_conds)
                df = client.query(final_sql).to_dataframe()
                if not df.empty:
                    st.success(df['summary_text'].iloc[0])
                    col_r, col_l = st.columns(2, gap="medium")
                    with col_r:
                        st.subheader("פירוט לפי עונות")
                        det_df = df[['קבוצה', 'עונה']].drop_duplicates().sort_values(['עונה', 'קבוצה'], ascending=[False, True])
                        st.dataframe(det_df, use_container_width=True, hide_index=True, column_order=("עונה", "קבוצה"))
                    with col_l:
                        st.subheader("סיכום הצטברות")
                        sum_table = df[['מספר מקרים', 'קבוצות']].drop_duplicates().dropna().sort_values('מספר מקרים', ascending=False)
                        st.dataframe(
                            sum_table, 
                            use_container_width=True, 
                            hide_index=True, 
                            column_order=("מספר מקרים", "קבוצות"),
                            column_config={"מספר מקרים": st.column_config.Column(width="small")}
                        )
                else:
                    st.warning("אין תוצאות המשלבות את כל התנאים שנבחרו.")
            except Exception as e:
                st.error(f"שגיאה בהרצת השאילתה: {e}")
    else:
        st.info("הוסף קריטריון אחד לפחות כדי להתחיל בניתוח.")
