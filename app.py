import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import os

# 1. הגדרות עמוד (RTL ופריסה רחבה)
st.set_page_config(
    page_title="Football Analytics System", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

def fix_private_key(key):
    """מתקן את פורמט המפתח הפרטי כדי שיתאים לסטנדרט PEM של גוגל"""
    if not key:
        return None
    processed_key = key.replace("\\n", "\n").strip()
    if processed_key.count("\n") > 5:
        return processed_key
    header = "-----BEGIN PRIVATE KEY-----"
    footer = "-----END PRIVATE KEY-----"
    content = processed_key.replace(header, "").replace(footer, "").replace("\n", "").strip()
    lines = [content[i:i+64] for i in range(0, len(content), 64)]
    return f"{header}\n" + "\n".join(lines) + f"\n{footer}\n"

def get_bigquery_client():
    """אתחול הלקוח של BigQuery תוך שימוש ב-Secrets של Streamlit"""
    if "gcp_service_account" in st.secrets:
        try:
            info = dict(st.secrets["gcp_service_account"])
            info["private_key"] = fix_private_key(info.get("private_key", ""))
            credentials = service_account.Credentials.from_service_account_info(info)
            return bigquery.Client(credentials=credentials, project=info["project_id"])
        except Exception as e:
            st.error(f"❌ שגיאה באתחול ההרשאות: {e}")
            return None
    return None

client = get_bigquery_client()

# 2. ייבוא המודולים מתיקיית modules
try:
    from modules import streaks_ui, heavy_losses_ui, top_scorers_ui, league_table_ui
except ImportError as e:
    st.error(f"❌ שגיאה בייבוא מודולים: {e}")

# 3. פונקציית עזר לטעינת שאילתות SQL
def load_query(filename):
    query_path = os.path.join("sql", filename)
    if os.path.exists(query_path):
        with open(query_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def reset_cache():
    st.cache_data.clear()

# 4. תפריט ניווט צדדי
st.sidebar.title("⚽ מערכת ניתוח נתונים")
page = st.sidebar.radio("בחר כלי ניתוח:", [
    "🔥 מנוע רצפים", 
    "📉 תבוסות כבדות", 
    "🏆 מלכי השערים", 
    "📊 טבלת ליגה"
])

# 5. ניתוב לעמודים (וודא ששמות הפונקציות זהים בקבצי ה-UI)
if client:
    if page == "🔥 מנוע רצפים":
        sql = load_query("streaks.sql")
        if sql:
            streaks_ui.show_streaks_interface(client, sql, reset_cache)

    elif page == "📉 תבוסות כבדות":
        sql = load_query("heavy_losses.sql")
        if sql:
            heavy_losses_ui.show_losses_interface(client, sql)

    elif page == "🏆 מלכי השערים":
        sql = load_query("top_scorers.sql")
        if sql:
            top_scorers_ui.show_scorers_interface(client, sql_template, get_season_data, get_filter_options, reset_params)

    elif page == "📊 טבלת ליגה":
        sql = load_query("league_table.sql")
        if sql:
            league_table_ui.show_table_interface(
                client, 
                sql, 
                get_season_data=None # כאן צריך להעביר את הפונקציה שמחזירה את נתוני העונה
            )
else:
    st.warning("⚠️ לא ניתן להתחבר ל-BigQuery. וודא שהגדרת Secrets כראוי.")
