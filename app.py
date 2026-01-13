import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import json

# הגדרות עיצוב ליישור העמוד והטבלאות מימין לשמאל (RTL)
st.markdown("""
    <style>
    /* יישור כללי של העמוד לימין */
    .main {
        direction: RTL;
        text-align: right;
    }
    /* הפיכת כיוון הטבלאות מימין לשמאל */
    [data-testid="stDataFrame"] {
        direction: RTL;
    }
    /* יישור תפריט הצידי */
    section[data-testid="stSidebar"] {
        direction: RTL;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

# חיבור למפתח מתוך ה-Secrets של Streamlit
info = json.loads(st.secrets["gcp_service_account"]["json_data"])
credentials = service_account.Credentials.from_service_account_info(info)
client = bigquery.Client(credentials=credentials, project=info['project_id'])

# תפריט צידי
st.sidebar.title("תפריט שאילתות")
query_type = st.sidebar.selectbox("בחר שאילתה להרצה:", ["טבלת ליגה", "סטטיסטיקת כובשים"])

st.title(f"מערכת נתונים: {query_type}")

# --- הגדרות פילטרים בסרגל הצידי ---
st.sidebar.subheader("פילטרים")

comp_id = st.sidebar.text_input("הזן comp_id:", value="10")

if query_type == "טבלת ליגה":
    season = st.sidebar.number_input("עונה:", value=2026)
    col1, col2 = st.sidebar.columns(2)
    with col1:
        week_start = st.number_input("מחזור התחלה:", value=1)
    with col2:
        week_end = st.number_input("מחזור סיום:", value=40)
    
    limit_options = ["ללא הגבלה", 5, 10, 20, 50, 100]
    limit_choice = st.sidebar.selectbox("כמות תוצאות להצגה:", limit_options, index=0)

else:
    season_start = st.sidebar.number_input("מהעונה:", value=2003)
    season_end = st.sidebar.number_input("עד העונה (כולל):", value=202
