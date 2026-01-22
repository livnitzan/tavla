import streamlit as st
from google.cloud import bigquery
import os

# 1. הגדרות עמוד (RTL ופריסה רחבה)
st.set_page_config(page_title="Football Analytics System", layout="wide", initial_sidebar_state="expanded")

# 2. אתחול לקוח BigQuery
# בענן (Streamlit Cloud), הוא ישתמש ב-Secrets שתגדיר. מקומית הוא יחפש קובץ JSON.
client = bigquery.Client()

# 3. ייבוא המודולים מהתיקייה שיצרת
from modules import streaks_ui, heavy_losses_ui, top_scorers_ui, league_table_ui

# 4. פונקציית עזר לטעינת קבצי ה-SQL
def load_query(filename):
    query_path = os.path.join("sql", filename)
    if os.path.exists(query_path):
        with open(query_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

# 5. תפריט ניווט צדדי
st.sidebar.title("⚽ תפריט ניתוח נתונים")
page = st.sidebar.radio("בחר כלי ניתוח:", [
    "🔥 מנוע רצפים", 
    "📉 תבוסות כבדות", 
    "🏆 מלכי השערים", 
    "📊 טבלת ליגה"
])

# פונקציית איפוס מטמון (למקרה שנרצה לרענן נתונים)
def reset_cache():
    st.cache_data.clear()

# 6. ניתוב לעמוד הנבחר
if page == "🔥 מנוע רצפים":
    sql = load_query("streaks.sql")
    if sql:
        streaks_ui.show_streaks_interface(client, sql, reset_cache)
    else:
        st.error("קובץ streaks.sql לא נמצא בתיקיית sql")

elif page == "📉 תבוסות כבדות":
    sql = load_query("heavy_losses.sql")
    if sql:
        heavy_losses_ui.show_losses_interface(client, sql)
    else:
        st.error("קובץ heavy_losses.sql לא נמצא")

elif page == "🏆 מלכי השערים":
    sql = load_query("top_scorers.sql")
    if sql:
        top_scorers_ui.show_scorers_interface(client, sql)
    else:
        st.error("קובץ top_scorers.sql לא נמצא")

elif page == "📊 טבלת ליגה":
    sql = load_query("league_table.sql")
    if sql:
        league_table_ui.show_table_interface(client, sql)
    else:
        st.error("קובץ league_table.sql לא נמצא")
