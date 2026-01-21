import streamlit as st
import pandas as pd
import plotly.express as px # מניח שנשתמש בגרפים עבור התפלגות, אם בנינו

def show_scorers_interface(client, sql_template):
    st.title("🏆 מלכי השערים (Top Scorers)")

    st.markdown("""
        <style>
            .scorer-header { text-align: center; color: #888; font-size: 13px; border-bottom: 1px solid #eee; padding-bottom: 4px; }
            .scorer-cell { text-align: center; font-size: 16px; font-weight: 500; }
            [data-testid="stHorizontalBlock"] { direction: rtl; }
            .scorer-row-wrap { width: 100%; padding: 10px 0px; border-bottom: 1px solid #f0f0f0; display: block; }
            
            /* סגנון לפופאובר של שחקן ספציפי */
            .player-summary-box {
                background-color: #f0f8ff; /* כחול בהיר */
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 15px;
                display: flex;
                flex-direction: row;
                justify-content: space-around;
                border: 1px solid #e0efff;
                direction: rtl;
            }
            .player-summary-item { display: flex; flex-direction: column; align-items: center; }
            .player-summary-label { font-size: 12px; color: #666; margin-bottom: 4px; }
            .player-summary-value { font-size: 16px; font-weight: bold; color: #007bff; }
        </style>
    """, unsafe_allow_html=True)

    # טעינת רשימת עונות ומפעלים זמינים (אפשר לשלוף מ-BigQuery או להגדיר סטטי)
    # לצורך הדוגמה נגדיר סטטי:
    available_seasons = sorted(list(range(datetime.now().year, 2000, -1)))
    available_comps = {10: "ליגת העל", 11: "גביע המדינה", 1: "אירופה"}
    
    with st.expander("🛠️ הגדרות סינון", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_season = st.selectbox("בחר עונה:", ["כל הזמנים"] + available_seasons, index=1)
        with col2:
            selected_comps_names = st.multiselect("מפעלים:", list(available_comps.values()), default=["ליגת העל"])
        
        min_goals = st.slider("מינימום שערים:", 1, 30, 5)
        limit_val = st.selectbox("הצג טופ:", [20, 50, 100], index=0)

    # המרה של שמות המפעלים ל-ID
    selected_comp_ids = [k for k, v in available_comps.items() if v in selected_comps_names]
    comp_filter_sql = f"AND comp_id IN ({','.join(map(str, selected_comp_ids))})" if selected_comp_ids else ""
    season_filter_sql = f"AND season = {selected_season}" if selected_season != "כל הזמנים" else ""

    if st.button("🚀 חפש כובשים", type="primary", use_container_width=True):
        query = sql_template.replace("{season_filter}", season_filter_sql)\
                              .replace("{comp_filter}", comp_filter_sql)\
                              .replace("{min_goals}", str(min_goals))\
                              .replace("{limit}", str(limit_val))
        
        with st.spinner("מחשב מלכי שערים..."):
            df = client.query(query).to_dataframe()
            st.session_state.last_scorers = df

    if "last_scorers" in st.session_state and st.session_state.last_scorers is not None:
        df = st.session_state.last_scorers
        st.markdown("---")
        
        # כותרות הטבלה
        h_cols = st.columns([0.5, 2, 1.5, 1, 0.5])
        headers = ["#", "שחקן", "קבוצה", "שערים", ""]
        for col, h in zip(h_cols, headers):
            col.markdown(f"<div class='scorer-header'>{h}</div>", unsafe_allow_html=True)

        for idx, row in df.iterrows():
            with st.container():
                st.markdown('<div class="scorer-row-wrap">', unsafe_allow_html=True)
                r_cols = st.columns([0.5, 2, 1.5, 1, 0.5])
                
                r_cols[0].markdown(f"<div class='scorer-cell'>{idx + 1}</div>", unsafe_allow_html=True)
                r_cols[1].markdown(f"<div class='scorer-cell'>{row['שחקן']}</div>", unsafe_allow_html=True)
                r_cols[2].markdown(f"<div class='scorer-cell'>{row['קבוצה']}</div>", unsafe_allow_html=True)
                r_cols[3].markdown(f"<div class='scorer-cell' style='color:#007bff; font-weight:bold;'>{row['שערים']}</div>", unsafe_allow_html=True)
                
                with r_cols[4].popover("⌄"):
                    st.subheader(f"⚽ פירוט שערים: {row['שחקן']}")
                    
                    # הצגת סיכום לשחקן
                    st.markdown(f"""
                        <div class="player-summary-box">
                            <div class="player-summary-item"><span class="player-summary-label">סה"כ שערים</span><span class="player-summary-value">{row['שערים']}</span></div>
                            <div class="player-summary-item"><span class="player-summary-label">ממוצע למשחק</span><span class="player-summary-value">{(row['שערים'] / row['משחקים']):.2f}</span></div>
                        </div>
                    """, unsafe_allow_html=True)

                    # כאן היית יכול להוסיף טבלת פירוט שערים (תאריך, יריבה, סוג שער וכו')
                    # אם נרצה לפתח את זה יותר, נצטרך לשלוף את הנתונים האלו ב-SQL
                    st.info("פירוט משחקים ושערים ספציפיים לשחקן יפותח בהמשך.")
                st.markdown('</div>', unsafe_allow_html=True)

from datetime import datetime # ייבוא עבור datetime.now().year
