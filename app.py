import streamlit as st
from google.cloud import bigquery
import os

# --- הגדרות יישור לימין (RTL) ---
st.markdown("""
    <style>
    .main { direction: RTL; text-align: right; }
    [data-testid="stDataFrame"] { direction: RTL; }
    section[data-testid="stSidebar"] { direction: RTL; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# חיבור למפתח - בדיוק כפי ששלחת
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "creds.json"
client = bigquery.Client()

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
    season_end = st.sidebar.number_input("עד העונה (כולל):", value=2026)
    is_winner = st.sidebar.checkbox("רק Winner?", value=True)
    winner_condition = "AND winner" if is_winner else ""
    order_type = st.sidebar.selectbox("בחר order_type:", ["last", "first", "all"], index=0)
    excluded_names = st.sidebar.text_input("שמות להחרגה:", value="טכני, עצמי")
    names_list = ", ".join([f"'{name.strip()}'" for name in excluded_names.split(",")])
    
    limit_options = [5, 10, 20, 50, 100, "ללא הגבלה"]
