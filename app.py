import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import os

# הגדרות עמוד - זה חייב לרוץ ראשון כדי שהתפריט יופיע
st.set_page_config(page_title="Football Analytics", layout="wide")

# פונקציית התיקון למפתח
def fix_private_key(key):
    if not key: return None
    processed_key = key.replace("\\n", "\n").strip()
    return processed_key if "-----BEGIN" in processed_key else f"-----BEGIN PRIVATE KEY-----\n{processed_key}\n-----END PRIVATE KEY-----"

# חיבור ל-BigQuery
def get_bigquery_client():
    if "gcp_service_account" in st.secrets:
        try:
            info = dict(st.secrets["gcp_service_account"])
            info["private_key"] = fix_private_key(info.get("private_key", ""))
            credentials = service_account.Credentials.from_service_account_info(info)
            return bigquery.Client(credentials=credentials, project=info["project_id"])
        except Exception as e:
            st.error(f"שגיאה בחיבור: {e}")
    return None

client = get_bigquery_client()

# ייבוא בטוח - כדי שהתפריט לא ייעלם אם יש שגיאה במודולים
try:
    from modules import streaks_ui, heavy_losses_ui, top_scorers_ui, league_table_ui
    from modules.logic import get_season_data, get_filter_options, reset_params
except Exception as e:
    st.sidebar.error(f"שגיאה בטעינת מודולים: {e}")
    # הגדרת פונקציות ריקות כדי שהקוד לא יקרוס
    get_season_data = lambda *args: {}
    get_filter_options = lambda *args: ({}, {})
    reset_params = lambda: None

# ציור התפריט - עכשיו הוא בטוח יופיע
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
        if sql: top_scorers_ui.show_scorers_interface(client, sql_template, get_season_data, get_filter_options, reset_params)

    elif page == "📊 טבלת ליגה":
        sql = load_query("league_table.sql")
        if sql:
            league_table_ui.show_table_interface(client, sql, get_season_data)
