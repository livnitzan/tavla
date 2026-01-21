import streamlit as st
import pandas as pd

def show_table_interface(client, sql_template):
    st.title("📊 טבלת ליגה דינמית")

    # CSS לעיצוב טבלת הליגה (כולל הדגשת מקומות ראשונים וצבעי תוצאות)
    st.markdown("""
        <style>
            .league-table-container { direction: rtl; }
            .league-header { text-align: center; color: #888; font-size: 13px; font-weight: bold; border-bottom: 2px solid #eee; padding: 10px 0; }
            .league-cell { text-align: center; font-size: 15px; padding: 8px 0; border-bottom: 1px solid #f9f9f9; }
            .pos-top { color: #28a745; font-weight: bold; } /* מקום ראשון/אירופה */
            .pos-bottom { color: #dc3545; font-weight: bold; } /* ירידה */
            .team-name { text-align: right; padding-right: 15px; font-weight: 600; }
            
            /* עיצוב שורת הטבלה */
            .league-row:hover { background-color: #f1f3f6 !important; }
        </style>
    """, unsafe_allow_html=True)

    # פילטרים לבחירת עונה ומפעל
    with st.expander("🔍 הגדרות טבלה", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            # שליפת רשימת עונות (אפשר להחליף בשאילתה דינמית)
            selected_season = st.selectbox("בחר עונה:", range(2025, 1990, -1), index=1)
        with col2:
            # בדרך כלל טבלה רלוונטית רק לליגה (ID 10)
            comp_id = st.selectbox("מפעל:", [10], format_func=lambda x: "ליגת העל")

    if st.button("🚀 טען טבלת ליגה", type="primary", use_container_width=True):
        # החלפת הפרמטרים בשאילתה
        query = sql_template.replace("{season}", str(selected_season)).replace("{comp_id}", str(comp_id))
        
        with st.spinner(f"מחשב טבלה לעונת {selected_season}..."):
            df = client.query(query).to_dataframe()
            st.session_state.last_table = df

    if "last_table" in st.session_state and st.session_state.last_table is not None:
        df = st.session_state.last_table
        st.markdown("---")
        
        # יצירת מבנה עמודות לטבלה (מיקום, קבוצה, משחקים, נצ', תיקו, הפס', שערים, הפרש, נקודות)
        t_cols = st.columns([0.5, 2, 0.6, 0.6, 0.6, 0.6, 1.2, 0.8, 0.8])
        headers = ["#", "קבוצה", "מש'", "נצ'", "ת'", "הפ'", "שערים", "הפרש", "נק'"]
        
        for col, h in zip(t_cols, headers):
            col.markdown(f"<div class='league-header'>{h}</div>", unsafe_allow_html=True)

        for idx, row in df.iterrows():
            pos = idx + 1
            # קביעת מחלקת CSS לפי מיקום
            pos_class = "pos-top" if pos <= 3 else ("pos-bottom" if pos > len(df)-2 else "")
            
            with st.container():
                r_cols = st.columns([0.5, 2, 0.6, 0.6, 0.6, 0.6, 1.2, 0.8, 0.8])
                
                r_cols[0].markdown(f"<div class='league-cell {pos_class}'>{pos}</div>", unsafe_allow_html=True)
                r_cols[1].markdown(f"<div class='league-cell team-name'>{row['קבוצה']}</div>", unsafe_allow_html=True)
                r_cols[2].markdown(f"<div class='league-cell'>{row['משחקים']}</div>", unsafe_allow_html=True)
                r_cols[3].markdown(f"<div class='league-cell'>{row['ניצחונות']}</div>", unsafe_allow_html=True)
                r_cols[4].markdown(f"<div class='league-cell'>{row['תיקו']}</div>", unsafe_allow_html=True)
                r_cols[5].markdown(f"<div class='league-cell'>{row['הפסדים']}</div>", unsafe_allow_html=True)
                r_cols[6].markdown(f"<div class='league-cell'>{row['שערי_זכות']}-{row['שערי_חובה']}</div>", unsafe_allow_html=True)
                
                # הפרש שערים עם צבע (ירוק לחיובי, אדום לשלילי)
                diff = row['הפרש_שערים']
                diff_color = "#28a745" if diff > 0 else ("#dc3545" if diff < 0 else "#888")
                r_cols[7].markdown(f"<div class='league-cell' style='color:{diff_color};'>{diff:+}</div>", unsafe_allow_html=True)
                
                r_cols[8].markdown(f"<div class='league-cell' style='font-weight:bold;'>{row['נקודות']}</div>", unsafe_allow_html=True)
                
                st.markdown('<div style="border-bottom: 1px solid #f0f0f0; width: 100%;"></div>', unsafe_allow_html=True)

        # אפשרות להורדת הטבלה
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 הורד טבלה כ-CSV",
            data=csv,
            file_name=f"league_table_{selected_season}.csv",
            mime='text/csv',
        )
