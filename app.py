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

# 2. אתחול לקוח BigQuery עם מנגנון תיקון לשגיאת binascii
def get_bigquery_client():
    if "gcp_service_account" in st.secrets:
        # שליפת פרטי ה-Service Account מה-Secrets
        info = dict(st.secrets["gcp_service_account"])
        
        # תיקון קריטי: החלפת מחרוזת ה-slash-n בתו ירידת שורה אמיתי
        # זה הפתרון הישיר לשגיאת binascii.Error: a2b_base64
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        try:
            credentials = service_account.Credentials.from_service_account_info(info)
            return bigquery.Client(credentials=credentials, project=info["project_id"])
        except Exception as e:
            st.error(f"שגיאה באתחול ההרשאות: {e}")
            return None
    else:
        # למקרה של הרצה מקומית עם משתני סביבה סטנדרטיים
        try:
            return bigquery.Client()
        except Exception as e:
            st.error("לא נמצאו הרשאות BigQuery. וודא שהגדרת Secrets ב-Streamlit Cloud.")
            return None

client = get_bigquery_client()

# 3. ייבוא המודולים מהתיקייה שיצרת
# (וודא שקיימת תיקיית modules עם קובץ __init__.py ריק בפנים)
try:
    from modules import streaks_ui, heavy_losses_ui, top_scorers_ui, league_table_ui
except ImportError as e:
    st.error(f"שגיאה בייבוא מודולים: {e}. וודא שתיקיית modules קיימת עם קובץ __init__.py")

# 4. פונקציית עזר לטעינת קבצי ה-SQL מתיקיית sql
def load_query(filename):
    query_path = os.path.join("sql", filename)
    if os.path.exists(query_path):
        with open(query_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

# פונקציית ריענון מטמון
def reset_cache():
    st.cache_data.clear()
    st.success("המטמון נוקה בהצלחה")

# 5. תפריט ניווט צדדי
st.sidebar.title("⚽ מערכת ניתוח נתונים")
page = st.sidebar.radio("בחר כלי ניתוח:", [
    "🔥 מנוע רצפים", 
    "📉 תבוסות כבדות", 
    "🏆 מלכי השערים", 
    "📊 טבלת ליגה"
])

# 6. ניתוב לעמוד הנבחר והעברת ה-client והשאילתות
if client:
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
            st.error("קובץ heavy_losses.sql לא נמצא בתיקיית sql")

    elif page == "🏆 מלכי השערים":
        sql = load_query("top_scorers.sql")
        if sql:
            top_scorers_ui.show_scorers_interface(client, sql)
        else:
            st.error("קובץ top_scorers.sql לא נמצא בתיקיית sql")

    elif page == "📊 טבלת ליגה":
        sql = load_query("league_table.sql")
        if sql:
            league_table_ui.show_table_interface(client, sql)
        else:
            st.error("קובץ league_table.sql לא נמצא בתיקיית sql")
else:
    st.warning("המתנה לחיבור תקין ל-BigQuery...")
