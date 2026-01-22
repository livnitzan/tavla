import streamlit as st
import pandas as pd

def show_league_table_interface(client, sql_template, get_season_data):
    st.title("🏆 טבלת הליגה")

    # CSS מעודכן עם תיקון לסימן המינוס
    st.markdown("""
        <style>
            .stTable {
                display: flex;
                justify-content: center;
                direction: rtl;
            }
            table {
                width: auto !important;
                border-collapse: collapse;
                margin-top: 20px;
                border: 1px solid #e6e9ef;
            }
            th, td {
                padding: 10px 15px !important;
                font-size: 1.05rem;
                border: 1px solid #f0f2f6;
                white-space: nowrap;
                text-align: center !important;
            }
            /* תיקון סימן המינוס: הגדרת עמודות המספרים כ-LTR */
            td:nth-child(n+3), th:nth-child(n+3), td:nth-child(1), th:nth-child(1) {
                direction: ltr !important;
                unicode-bidi: plaintext !important;
            }
            /* עמודת האינדקס (#) */
            th:nth-child(1), td:nth-child(1) {
                width: 45px !important;
                background-color: #f8f9fb;
                font-weight: bold;
            }
            /* עמודת שם הקבוצה - יישור לימין */
            th:nth-child(2), td:nth-child(2) {
                min-width: 160px !important;
                text-align: right !important;
                padding-right: 20px !important;
                direction: rtl !important; /* שם הקבוצה חייב להישאר RTL */
            }
            /* עמודות הנתונים */
            th:nth-child(n+3), td:nth-child(n+3) {
                width: 60px !important;
            }
            /* הבלטת עמודת הנקודות */
            th:last-child, td:last-child {
                font-weight: bold;
                background-color: #f0f7ff;
                width: 65px !important;
            }
            th {
                background-color: #f0f2f6;
                font-weight: bold;
            }
            div[data-testid="stColumn"] {
                display: flex;
                justify-content: center;
            }
        </style>
    """, unsafe_allow_html=True)

    season_dict = get_season_data()
    season_options = sorted(list(season_dict.keys()), reverse=True)

    _, col_a, col_b, _ = st.columns([2, 1, 1, 2])
    
    with col_a:
        selected_season = st.selectbox("בחר עונה:", season_options, index=0)
    with col_b:
        max_w = season_dict.get(selected_season, 30)
        selected_week = st.number_input("עד מחזור:", 1, max_w, max_w)

    try:
        query = sql_template.format(season=selected_season, max_week=selected_week)
        df = client.query(query).to_dataframe()

        if not df.empty:
            goal_label = "הפרש" if selected_season >= 1970 else "יחס"
            
            columns_order = [
                'team_name', 'gp', 'wins', 'draws', 'losses', 
                'gf_sum', 'ga_sum', 'goal_stat', 'points'
            ]
            
            display_df = df[columns_order].copy()
            display_df.columns = [
                'קבוצה', 'מש', 'נצ', 'תי', 'הפ', 'זכות', 'חובה', goal_label, 'נק'
            ]
            
            display_df.index = range(1, len(display_df) + 1)
            display_df.index.name = '#'

            st.table(display_df)

            if 'penalty_val' in df.columns:
                penalties = df[df['penalty_val'] != 0]
                if not penalties.empty:
                    st.markdown("<div style='text-align: center; width: 100%;'>", unsafe_allow_html=True)
                    st.write("---")
                    for _, row in penalties.iterrows():
                        pts = int(row['penalty_val'])
                        team_clean = row['team_name'].replace('*', '')
                        action = "הופחתו" if pts > 0 else "הוחזרו"
                        st.caption(f"ℹ️ ל{team_clean} {action} {abs(pts)} נקודות מנהלתיות.")
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("לא נמצאו נתונים.")
    except Exception as e:
        st.error(f"שגיאה: {e}")