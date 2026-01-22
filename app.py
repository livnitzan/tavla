import streamlit as st
from google.cloud import bigquery
import os
import glob

# ייבוא הממשקים
from logic import apply_custom_style, reset_params
from tpscr_ui import show_tpscr_interface
from heavy_ui import show_heavy_losses_interface
from streaks_ui import show_streaks_interface
from league_table_ui import show_league_table_interface 

# 1. הגדרות דף
st.set_page_config(page_title="מערכת נתוני כדורגל", layout="wide")
apply_custom_style()

# 2. חיבור ל-BigQuery
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "creds.json"
client = bigquery.Client()

# 3. פונקציות נתונים
@st.cache_data(ttl=3600)
def get_season_data():
    try:
        # ספירת מחזור מקסימלי לפי הכלל של 150 דקות
        query = """
            SELECT season, MAX(week) as max_week 
            FROM `table.srtdgms` 
            WHERE CAST(date AS TIMESTAMP) <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 150 MINUTE)
            GROUP BY season 
            ORDER BY season DESC
        """
        df = client.query(query).to_dataframe()
        return df.set_index('season')['max_week'].to_dict()
    except:
        return {2026: 19}

@st.cache_data(ttl=3600)
def get_filter_options():
    try:
        teams_df = client.query("SELECT team_id, team FROM `table.teams` WHERE team_id < 100 ORDER BY team ASC").to_dataframe()
        team_opts = dict(zip(teams_df['team'], teams_df['team_id']))
        stads_df = client.query("SELECT stad_id, stadium FROM `table.stads` ORDER BY stadium ASC").to_dataframe()
        stadium_opts = dict(zip(stads_df['stadium'], stads_df['stad_id']))
        return team_opts, stadium_opts
    except:
        return {}, {}

# 4. תפריט צד (Sidebar)
st.sidebar.title("⚽ תפריט שאילתות")
all_files = glob.glob("*.sql")
all_queries = {f: f.replace(".sql", "").replace("_", " ").upper() for f in all_files}

for f_id in sorted(all_queries.keys()):
    if st.sidebar.button(all_queries[f_id]):
        st.session_state.active_query = f_id
        st.rerun()

if 'active_query' not in st.session_state and all_queries:
    st.session_state.active_query = "league_table.sql" if "league_table.sql" in all_queries else sorted(list(all_queries.keys()))[0]

# 5. ניתוב (Routing)
if 'active_query' in st.session_state:
    active = st.session_state.active_query
    
    # טבלת ליגה
    if "league_table" in active:
        with open(active, 'r', encoding='utf-8-sig') as f:
            sql_template = f.read()
        show_league_table_interface(client, sql_template, get_season_data)
    
    # מלך השערים
    elif "tpscr" in active:
        with open(active, 'r', encoding='utf-8-sig') as f:
            sql_template = f.read()
        show_tpscr_interface(client, sql_template, get_season_data, get_filter_options, reset_params)
    
    # רצפים - כאן הוספתי את הקריאה לקובץ ה-SQL והעברה ל-UI
    elif "streaks" in active:
        with open(active, 'r', encoding='utf-8-sig') as f:
            sql_template = f.read()
        show_streaks_interface(client, sql_template, reset_params)
    
    # הפסדים כבדים
    elif "heavy_losses" in active:
        with open(active, 'r', encoding='utf-8-sig') as f:
            sql_template = f.read()
        show_heavy_losses_interface(client, sql_template)
        
    # שאילתות גנריות אחרות שקיימות בתיקייה
    else:
        st.title(all_queries[active])
        if st.button("🚀 הרץ שאילתה"):
            with open(active, 'r', encoding='utf-8-sig') as f:
                raw_sql = f.read()
            with st.spinner("מריץ שאילתה..."):
                df = client.query(raw_sql).to_dataframe()
                st.table(df)
