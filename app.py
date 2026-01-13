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
    season_end = st.sidebar.number_input("עד העונה (כולל):", value=2026)
    is_winner = st.sidebar.checkbox("רק Winner?", value=True)
    winner_condition = "AND winner" if is_winner else ""
    order_type = st.sidebar.selectbox("בחר order_type:", ["last", "first", "all"], index=0)
    excluded_names = st.sidebar.text_input("שמות להחרגה:", value="טכני, עצמי")
    names_list = ", ".join([f"'{name.strip()}'" for name in excluded_names.split(",")])
    
    limit_options = [5, 10, 20, 50, 100, "ללא הגבלה"]
    limit_choice = st.sidebar.selectbox("כמות תוצאות להצגה:", limit_options, index=1)

limit_sql = "" if limit_choice == "ללא הגבלה" else f"LIMIT {limit_choice}"

# פונקציית צביעה לטבלת ליגה
def color_league_table(df):
    colors = ['' for _ in range(len(df))]
    if len(df) > 0:
        colors[0] = 'background-color: #ADD8E6' 
        if len(df) >= 2:
            colors[-1] = 'background-color: #FFB6C1'
            colors[-2] = 'background-color: #FFB6C1'
    return df.style.apply(lambda x: colors, axis=0)

def run_query():
    if query_type == "טבלת ליגה":
        QUERY = f'''
        SELECT row_number() over (partition by t0.season order by plf.plf, pts desc, gdf desc, Ws desc, gf desc) as rk
                ,case when ddct=0 then tms.team else concat(tms.team || " (*)") end as team
                ,Ws, Ds, Ls, gf, ga, gdf, pts
        FROM (
            SELECT gms.season, gms.team, count(gms.team) as games
                  ,sum(case when date < current_date() and res="W" then 1 else 0 end) as Ws
                  ,sum(case when date < current_date() and res="D" then 1 else 0 end) as Ds
                  ,sum(case when date < current_date() and res="L" then 1 else 0 end) as Ls
                  ,sum(gf) as gf, sum(ga) as ga, sum(gf)-sum(ga) as gdf
                  ,cast(ceil(sum(case 
                        when date < current_date() and res="W" then (case when gms.season>1982 then (case when gms.season in (2010, 2011) and plf=10 then 1.5 else 3 end) else 2 end)
                        when date < current_date() and res="D" then (case when gms.forfeit=true then 0 else (case when gms.season in (2010, 2011) and plf=10 then 0.5 else 1 end) end)
                        else 0 end) - coalesce(dct.pts, 0)) as int64) as pts
                  ,coalesce(dct.pts, 0) as ddct
            FROM `table.srtdgms` as gms
            LEFT JOIN (SELECT season, team, sum(pts) as pts FROM `table.ddctn` GROUP BY season, team) as dct
              ON gms.season=dct.season AND gms.team=dct.team
            WHERE gms.season = {season}
              AND gms.comp_id = {comp_id}
              AND gms.week BETWEEN {week_start} AND {week_end}
