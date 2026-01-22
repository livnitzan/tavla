import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import os

# הגדרות עמוד
st.set_page_config(page_title="Football Analytics System", layout="wide", initial_sidebar_state="expanded")

# פונקציה לאתחול הלקוח עם ה-Secrets
def get_bigquery_client():
    if "gcp_service_account" in st.secrets:
        # שליפת המפתח מה-Secrets של Streamlit
        info = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(info)
        return bigquery.Client(credentials=credentials, project=info["project_id"])
    else:
        # למקרה שאתה מריץ מקומי ואין Secrets
        return bigquery.Client()

client = get_bigquery_client()

# ייבוא המודולים מהתיקייה
from modules import streaks_ui, heavy_losses_ui, top_scorers_ui, league_table_ui

# פונקציית עזר לטעינת קבצי ה-SQL
def load_query(filename):
    query_path = os.path.join("sql", filename)
    if os.path.exists(query_path):
        with open(query_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

# תפריט ניווט
st.sidebar.title("⚽ תפריט ניתוח")
page = st.sidebar.radio("בחר כלי:", ["🔥 מנוע רצפים", "📉 תבוסות כבדות", "🏆 מלכי השערים", "📊 טבלת ליגה"])

if page == "🔥 מנוע רצפים":
    sql = load_query("streaks.sql")
    if sql: streaks_ui.show_streaks_interface(client, sql, lambda: st.cache_data.clear())
elif page == "📉 תבוסות כבדות":
    sql = load_query("heavy_losses.sql")
    if sql: heavy_losses_ui.show_losses_interface(client, sql)
elif page == "🏆 מלכי השערים":
    sql = load_query("top_scorers.sql")
    if sql: top_scorers_ui.show_scorers_interface(client, sql)
elif page == "📊 טבלת ליגה":
    sql = load_query("league_table.sql")
    if sql: league_table_ui.show_table_interface(client, sql)
