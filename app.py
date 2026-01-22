import streamlit as st
import os

# 1. זה חייב להיות הדבר הראשון בקוד כדי שהתפריט יופיע
st.set_page_config(page_title="Football Analytics", layout="wide")

# 2. ייבוא בטוח - אם המודולים שבורים, התפריט עדיין יופיע ותקבל הודעת שגיאה
try:
    from modules import streaks_ui, heavy_losses_ui, top_scorers_ui, league_table_ui
    from modules.logic import get_season_data, get_filter_options, reset_params
except Exception as e:
    st.sidebar.error(f"⚠️ שגיאה בטעינת המודולים: {e}")
    # הגדרת פונקציות "דמי" כדי שהקוד לא יקרוס בהמשך
    get_season_data = lambda *args: {}
    get_filter_options = lambda *args: ({}, {})
    reset_params = lambda: None

# 3. ציור התפריט - עכשיו הוא יופיע בכל מקרה
st.sidebar.title("⚽ תפריט ניווט")
page = st.sidebar.radio("בחר כלי ניתוח:", [
    "🔥 מנוע רצפים", 
    "📉 תבוסות כבדות", 
    "🏆 מלכי השערים", 
    "📊 טבלת ליגה"
])

def load_query(filename):
    path = os.path.join("sql", filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f: return f.read()
    return None

# ניווט
if client:
    if page == "🔥 מנוע רצפים":
        sql = load_query("streaks.sql")
        if sql: streaks_ui.show_streaks_interface(client, sql, st.cache_data.clear)

    elif page == "📉 תבוסות כבדות":
        sql = load_query("heavy_losses.sql")
        if sql: heavy_losses_ui.show_losses_interface(client, sql)

    elif page == "🏆 מלכי השערים":
        sql = load_query("top_scorers.sql")
        if sql:
            # כאן אנחנו שולחים את הפונקציות עצמן כפרמטרים
            top_scorers_ui.show_scorers_interface(client, sql, get_season_data, get_filter_options, reset_params)

    elif page == "📊 טבלת ליגה":
        sql = load_query("league_table.sql")
        if sql:
            league_table_ui.show_table_interface(client, sql, get_season_data)
