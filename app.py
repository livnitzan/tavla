import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import os
import glob

# 1. הגדרות דף - חייב להיות השורה הראשונה
st.set_page_config(page_title="מערכת נתוני כדורגל", layout="wide")

# ייבוא פונקציות עזר ו-UI
import logic
import heavy_ui
import league_table_ui
import streaks_ui
import tpscr_ui

logic.apply_custom_style()

# 2. חיבור ל-BigQuery (מותאם לענן סטרימליט באמצעות Secrets)
def get_bigquery_client():
    if "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        # תיקון לפורמט ה-Private Key
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        credentials = service_account.Credentials.from_service_account_info(info)
        return bigquery.Client(credentials=credentials, project=info["project_id"])
    # Fallback למחשב מקומי אם קיים קובץ JSON
    elif os.path.exists("creds.json"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "creds.json"
        return bigquery.Client()
    return None

client = get_bigquery_client()

# 3. פונקציות נתונים מרכזיות
@st.cache_data(ttl=3600)
def get_season_data():
    if not client: return {2026: 19}
    try:
        query = """
            SELECT season, MAX(week) as max_week 
            FROM `tavla-440015.table.srtdgms` 
            WHERE CAST(date AS TIMESTAMP) <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 150 MINUTE)
            GROUP BY season 
            ORDER BY season DESC
        """
        df = client.query(query).to_dataframe()
        return df.set_index('season')['max_week'].to_dict()
    except Exception as e:
        return {2026: 19}

@st.cache_data(ttl=3600)
def get_filter_options():
    if not client: return {}, {}
    try:
        teams_df = client.query("SELECT team_id, team FROM `tavla-440015.table.teams` WHERE team_id < 100 ORDER BY team ASC").to_dataframe()
        team_opts = dict(zip(teams_df['team'], teams_df['team_id']))
        stads_df = client.query("SELECT stad_id, stadium FROM `tavla-440015.table.stads` ORDER BY stadium ASC").to_dataframe()
        stadium_opts = dict(zip(stads_df['stadium'], stads_df['stad_id']))
        return team_opts, stadium_opts
    except:
        return {}, {}

# 4. תפריט צד
st.sidebar.title("⚽ תפריט שאילתות")
# חיפוש קבצי SQL בתיקיית sql (כפי שמופיע בנתיבים שלך)
all_files = glob.glob("sql/*.sql")
all_queries = {f: os.path.basename(f).replace(".sql", "").replace("_", " ").upper() for f in all_files}

for f_path in sorted(all_queries.keys()):
    if st.sidebar.button(all_queries[f_path]):
        st.session_state.active_query = f_path
        st.rerun()

if 'active_query' not in st.session_state and all_queries:
    # ברירת מחדל
    st.session_state.active_query = next((f for f in all_queries if "league_table" in f), list(all_queries.keys())[0])

# 5. ניתוב (Routing) - שליחת הפונקציות כפרמטרים
if client and 'active_query' in st.session_state:
    active = st.session_state.active_query
    with open(active, 'r', encoding='utf-8-sig') as f:
        sql_template = f.read()

    if "league_table" in active:
        league_table_ui.show_league_table_interface(client, sql_template, get_season_data)
    
    elif "tpscr" in active:
        tpscr_ui.show_tpscr_interface(client, sql_template, get_season_data, get_filter_options, logic.reset_params)
    
    elif "streaks" in active:
        streaks_ui.show_streaks_interface(client, sql_template, logic.reset_params)
    
    elif "heavy_losses" in active:
        heavy_ui.show_heavy_losses_interface(client, sql_template)
