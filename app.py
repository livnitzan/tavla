import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import os

# 1. הגדרות עמוד (Layout רחב ותמיכה ב-RTL)
st.set_page_config(
    page_title="Football Analytics System", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

def fix_private_key(key):
    """
    מתקן את פורמט המפתח הפרטי כדי שיתאים לסטנדרט PEM של גוגל.
    מטפל בבעיות של סלאשים כפולים (\\n) ובפורמט שורה אחת שנוצר ב-Secrets.
    """
    if not key:
        return None
    
    # החלפת מחרוזת ה-slash-n (כטקסט) בירידת שורה אמיתית
    processed_key = key.replace("\\n", "\n")
    
    # ניקוי רווחים מיותרים בתחילה ובסוף
    processed_key = processed_key.strip()
    
    # אם המפתח כבר נראה תקין (כולל מספר ירידות שורה), נחזיר אותו ככה
    if processed_key.count("\n") > 5:
        return processed_key
        
    # אם הוא הגיע כשורה אחת ארוכה, נבנה אותו מחדש בפורמט PEM תקין (64 תווים לשורה)
    header = "-----BEGIN PRIVATE KEY-----"
    footer = "-----END PRIVATE KEY-----"
    
    # חילוץ התוכן שבין הכותרות
    content = processed_key.replace(header, "").replace(footer, "").replace("\n", "").strip()
    
    # פיצול תוכן המפתח לשורות של 64 תווים (סטנדרט PEM)
    lines = [content[i:i+64] for i in range(0, len(content), 64)]
    
    return f"{header}\n" + "\n".join(lines) + f"\n{footer}\n"

def get_bigquery_client():
    """אתחול הלקוח של BigQuery תוך שימוש ב-Secrets של Streamlit"""
    if "gcp_service_account" in st.secrets:
        try:
            # יצירת דיקשנרי חדש מה-Secrets כדי לא לשנות את המקור
            info = dict(st.secrets["gcp_service_account"])
            
            # תיקון המפתח הפרטי
            info["private_key"] = fix_private_key(info.get("private_key", ""))
            
            # יצירת הרשאות
            credentials = service_account.Credentials.from_service_account_info(info)
            return bigquery.Client(credentials=credentials, project=info["project_id"])
        except Exception as e:
            st.error(f"❌ שגיאה באתחול ההרשאות: {e}")
            return None
    else:
        st.warning("⚠️ לא נמצאו Secrets תחת 'gcp_service_account'. וודא שהגדרת אותם בלוח הבקרה.")
        return None

# אתחול הלקוח
client = get_bigquery_client()

# 2. ייבוא המודולים מתיקיית modules
# וודא שבתיקיית modules קיימים הקבצים וקובץ __init__.py ריק
try:
    from modules import streaks_ui, heavy_losses_ui, top_scorers_ui, league_table_ui
except ImportError as e:
    st.error(f"❌ שגיאה בייבוא מודולים: {e}. וודא שתיקיית modules קיימת ב-GitHub.")

# 3. פונקציית עזר לטעינת שאילתות SQL מתיקיית sql
def load_query(filename):
    query_path = os.path.join("sql", filename)
    if os.path.exists(query_path):
        with open(query_path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def reset_cache():
    st.cache_data.clear()

# 4. תפריט ניווט צדדי (Sidebar)
st.sidebar.title("⚽ ניתוח כדורגל")
st.sidebar.markdown("מערכת ניהול וסטטיסטיקה")

page = st.sidebar.radio("בחר כלי ניתוח:", [
    "🔥 מנוע רצפים", 
    "📉 תבוסות כבדות", 
    "🏆 מלכי השערים", 
    "📊 טבלת ליגה"
])

# 5. הצגת התוכן לפי העמוד הנבחר
if client:
    if page == "🔥 מנוע רצפים":
        sql = load_query("streaks.sql")
        if sql:
            streaks_ui.show_streaks_interface(client, sql, reset_cache)
        else:
            st.error("קובץ streaks.sql חסר בתיקיית sql")

    elif page == "📉 תבוסות כבדות":
        sql = load_query("heavy_losses.sql")
        if sql:
            heavy_losses_ui.show_losses_interface(client, sql)
        else:
            st.error("קובץ heavy_losses.sql חסר בתיקיית sql")

    elif page == "🏆 מלכי השערים":
        sql = load_query("top_scorers.sql")
        if sql:
            top_scorers_ui.show_scorers_interface(client, sql)
        else:
            st.error("קובץ top_scorers.sql חסר בתיקיית sql")

    elif page == "📊 טבלת ליגה":
        sql = load_query("league_table.sql")
        if sql:
            league_table_ui.show_table_interface(client, sql)
        else:
            st.error("קובץ league_table.sql חסר בתיקיית sql")
else:
    st.info("ממתין לחיבור תקין למסד הנתונים...")
