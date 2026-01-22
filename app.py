import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import os
import glob

# 1. הגדרות דף - חייב להיות ראשון
st.set_page_config(page_title="מערכת נתוני כדורגל", layout="wide")

# ייבוא הממשקים והלוגיקה
from logic import apply_custom_style, reset_params
from tpscr_ui import show_tpscr_interface
from heavy_ui import show_heavy_losses_interface
from streaks_ui import show_streaks_interface
from league_table_ui import show_league_table_interface 

apply_custom_style()

# 2. חיבור ל-BigQuery (מותאם לענן)
def get_bigquery_client():
    if "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        credentials = service_account.Credentials.from_service_account_info(info)
        return bigquery.Client(credentials=credentials, project=info["project_id"])
    elif os.path.exists("creds.json"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "creds.json"
        return bigquery.Client()
    return None

client = get_bigquery_client()

# 3. פונקציות נתונים (הזרקת ה-client)
@st.cache_data(ttl=3600)
def get_season_data():
    try:
        query = """
            SELECT season, MAX(week) as max_week 
            FROM `tavla-440015.table.srtdgms` 
            WHERE CAST(date AS TIMESTAMP) <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 150 MINUTE)
            GROUP BY season ORDER BY season DESC
        """
        df = client.query(query).to_dataframe()
        return df.set_index('season')['max_week'].to_dict()
    except:
        return {2026: 19}

@st.cache_data(ttl=3600)
def get_filter_options():
    try:
        t_df = client.query("SELECT team_id, team FROM `tavla-440015.table.teams` WHERE team_id < 100 ORDER BY team").to_dataframe()
        s_df = client.query("SELECT stad_id, stadium FROM `tavla-440015.table.stads` ORDER BY stadium").to_dataframe()
        return dict(zip(t_df['team'], t_df['team_id'])), dict(zip(s_df['stadium'], s_df['stad_id']))
    except:
        return {}, {}

# 4. תפריט צד וטעינת SQL
st.sidebar.title("⚽ תפריט שאילתות")
# מחפש קבצים בתיקייה הראשית (כפי שהעלית)
all_files = glob.glob("*.sql")
all_queries = {f: f.replace(".sql", "").replace("_", " ").upper() for f in all_files}

if not st.session_state.get('active_query') and all_queries:
    st.session_state.active_query = "league_table.sql" if "league_table.sql" in all_queries else list(all_queries.keys())[0]

for f_path, name in sorted(all_queries.items()):
    if st.sidebar.button(name, key=f_path):
        st.session_state.active_query = f_path
        st.rerun()

# 5. ניתוב לממשקים
if client and 'active_query' in st.session_state:
    active = st.session_state.active_query
    with open(active, 'r', encoding='utf-8-sig') as f:
        sql_template = f.read()
    
    if "league_table" in active:
        show_league_table_interface(client, sql_template, get_season_data)
    elif "tpscr" in active:
        show_tpscr_interface(client, sql_template, get_season_data, get_filter_options, reset_params)
    elif "streaks" in active:
        show_streaks_interface(client, sql_template, reset_params)
    elif "heavy_losses" in active:
        show_heavy_losses_interface(client, sql_template)
