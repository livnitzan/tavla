import streamlit as st
from google.cloud import bigquery
import os

# הגדרות עמוד
st.set_page_config(page_title="Football Analytics System", layout="wide", initial_sidebar_state="expanded")

# אתחול הלקוח - Streamlit יזהה אוטומטית את ה-Secrets בענן או את המפתח המקומי
client = bigquery.Client()

# ייבוא המודולים מהתיקייה (וודא שהם קיימים בגיטהאב תחת תיקיית modules)
from modules import streaks_ui, heavy_losses_ui, top_scorers_ui, league_table_ui

# פונקציית עזר לטעינת שאילתות
def load_query(filename):
    query_path = os.path.join("sql", filename)
    if os.path.exists(query_path):
        with open(query_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

# תפריט צדדי לניווט בין כל מה שבנינו
st.sidebar.title("⚽ תפריט ניתוח")
page = st.sidebar.radio("בחר כלי:", [
    "🔥 מנוע רצפים", 
    "📉 תבוסות כבדות (Heavy Losses)", 
    "🏆 כובשים מצטיינים (TPSCR)", 
    "📊 טבלת ליגה (Table)"
])

if page == "🔥 מנוע רצפים":
    sql = load_query("streaks.sql")
    if sql:
        streaks_ui.show_streaks_interface(client, sql, lambda: st.cache_data.clear())
    else:
        st.error("קובץ streaks.sql לא נמצא בתיקיית sql")

elif page == "📉 תבוסות כבדות (Heavy Losses)":
    sql = load_query("heavy_losses.sql")
    if sql:
        heavy_losses_ui.show_losses_interface(client, sql)

elif page == "🏆 כובשים מצטיינים (TPSCR)":
    sql = load_query("top_scorers.sql")
    if sql:
        top_scorers_ui.show_scorers_interface(client, sql)

elif page == "📊 טבלת ליגה (Table)":
    sql = load_query("league_table.sql")
    if sql:
        league_table_ui.show_table_interface(client, sql)
