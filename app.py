import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import os
import re

# 1. הגדרות עמוד
st.set_page_config(
    page_title="Football Analytics System", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. אתחול לקוח BigQuery עם ניקוי מפתח מתקדם
def get_bigquery_client():
    if "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        
        # ניקוי המפתח הפרטי מכל מה שעלול לשבור Base64
        if "private_key" in info:
            pk = info["private_key"]
            
            # א. החלפת מחרוזת ה-slash-n בתו ירידת שורה
            pk = pk.replace("\\n", "\n")
            
            # ב. ניקוי רווחים מיותרים בתחילת וסוף המפתח
            pk = pk.strip()
            
            # ג. תיקון קריטי: הסרת רווחים/טאבים שאולי נכנסו בין שורות המפתח
            # אנחנו שומרים על ירידות השורה אבל מנקים את מה שמסביבן
            lines = pk.split('\n')
            clean_lines = [line.strip() for line in lines if line.strip()]
            info["private_key"] = '\n'.join(clean_lines)
        
        try:
            credentials = service_account.Credentials.from_service_account_info(info)
            return bigquery.Client(credentials=credentials, project=info["project_id"])
        except Exception as e:
            st.error(f"שגיאה באתחול ההרשאות: {e}")
            return None
    else:
        try:
            return bigquery.Client()
        except:
            st.error("לא נמצאו הרשאות. הגדר Secrets ב-Streamlit Cloud.")
            return None

client = get_bigquery_client()

# 3. ייבוא מודולים
try:
    from modules import streaks_ui, heavy_losses_ui, top_scorers_ui, league_table_ui
except ImportError as e:
    st.error(f"שגיאה בייבוא מודולים: {e}")

# 4. עזרים
def load_query(filename):
    query_path = os.path.join("sql", filename)
    if os.path.exists(query_path):
        with open(query_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def reset_cache():
    st.cache_data.clear()

# 5. תפריט ניווט
st.sidebar.title("⚽ מערכת ניתוח")
page = st.sidebar.radio("בחר כלי:", ["🔥 מנוע רצפים", "📉 תבוסות כבדות", "🏆 מלכי השערים", "📊 טבלת ליגה"])

# 6. הצגת תוכן
if client:
    if page == "🔥 מנוע רצפים":
        sql = load_query("streaks.sql")
        if sql: streaks_ui.show_streaks_interface(client, sql, reset_cache)
    elif page == "📉 תבוסות כבדות":
        sql = load_query("heavy_losses.sql")
        if sql: heavy_losses_ui.show_losses_interface(client, sql)
    elif page == "🏆 מלכי השערים":
        sql = load_query("top_scorers.sql")
        if sql: top_scorers_ui.show_scorers_interface(client, sql)
    elif page == "📊 טבלת ליגה":
        sql = load_query("league_table.sql")
        if sql: league_table_ui.show_table_interface(client, sql)
