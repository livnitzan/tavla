import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import os
import glob
import json

# ייבוא הממשקים
from logic import apply_custom_style, reset_params
from tpscr_ui import show_tpscr_interface
from heavy_ui import show_heavy_losses_interface
from streaks_ui import show_streaks_interface
from league_table_ui import show_league_table_interface 

# 1. הגדרות דף
st.set_page_config(page_title="מערכת נתוני כדורגל", page_icon="logo.png", layout="wide")
apply_custom_style()

# 2. חיבור ל-BigQuery (התיקון הקריטי)
def get_bigquery_client():
    # בדיקה אם אנחנו באונליין (Streamlit Secrets)
    if "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        # תיקון תווים מיוחדים במפתח הפרטי
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        credentials = service_account.Credentials.from_service_account_info(info)
        return bigquery.Client(credentials=credentials, project=info["project_id"])
    
    # בדיקה אם אנחנו במחשב (קובץ מקומי)
    elif os.path.exists("creds.json"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "creds.json"
        return bigquery.Client()
    
    return None

client = get_bigquery_client()

# 3. פונקציות נתונים
@st.cache_data(ttl=3600)
def get_season_data():
    if not client: return {2026: 19}
    try:
        query = "SELECT season, MAX(week) as max_week FROM `tavla-440015.table.srtdgms` GROUP BY season ORDER BY season DESC"
        df = client.query(query).to_dataframe()
        return df.set_index('season')['max_week'].to_dict()
    except:
        return {2026: 19}

@st.cache_data(ttl=3600)
def get_filter_options():
    if not client: return {}, {}
    try:
        t_df = client.query("SELECT team_id, team FROM `tavla-440015.table.teams` WHERE team_id < 100 ORDER BY team").to_dataframe()
        s_df = client.query("SELECT stad_id, stadium FROM `tavla-440015.table.stads` ORDER BY stadium").to_dataframe()
        return dict(zip(t_df['team'], t_df['team_id'])), dict(zip(s_df['stadium'], s_df['stad_id']))
    except:
        return {}, {}

team_opts, stadium_opts = get_filter_options()

# --- עיצוב CSS ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    @media (max-width: 768px) {
        button[data-testid="stSidebarCollapseIcon"] {
            background-color: #3b82f6 !important;
            color: white !important;
            border-radius: 50% !important;
            width: 45px !important; height: 45px !important;
            position: fixed !important; top: 10px !important; right: 10px !important;
            z-index: 99999 !important;
        }
        button[data-testid="stSidebarCollapseIcon"] svg { fill: white !important; }
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] { display: flex; flex-direction: column; gap: 8px; }
    div[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: #ffffff; border: 1px solid #e0e0e0;
        padding: 10px 15px; border-radius: 8px; cursor: pointer;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] [data-checked="true"] > div {
        font-weight: bold; color: #3b82f6;
    }
    </style>
""", unsafe_allow_html=True)

# --- לוגיקת בחירת קובץ ---
sql_files = glob.glob("*.sql")
query_names = {os.path.basename(f).replace('.sql', '').replace('_', ' ').title(): f for f in sql_files}

if 'active_query' not in st.session_state:
    if sql_files:
        table_file = next((f for f in sql_files if "league_table" in f), sql_files[0])
        st.session_state.active_query = table_file

# --- הגדרות Sidebar ---
with st.sidebar:
    st.header("🔍 הגדרות גלובליות ⚙️")
    team_names = sorted(list(team_opts.keys()))
    full_team_list = ["ללא"] + team_names
    default_ix = next((i for i, name in enumerate(full_team_list) if name != "ללא" and team_opts.get(name) == 11), 0)
    current_team = st.selectbox("קבוצת ברירת מחדל:", options=full_team_list, index=default_ix)
    st.write("---")
    if query_names:
        selected_name = st.radio("בחר מנוע ניתוח:", list(query_names.keys()), 
                                index=list(query_names.values()).index(st.session_state.active_query))
        st.session_state.active_query = query_names[selected_name]

# 4. ניתוב (Routing)
if client and 'active_query' in st.session_state:
    active = st.session_state.active_query
    with open(active, 'r', encoding='utf-8-sig') as f:
        sql_template = f.read()

    if "league_table" in active:
        show_league_table_interface(client, sql_template, get_season_data, current_team)
    elif "tpscr" in active:
        show_tpscr_interface(client, sql_template, get_season_data, team_opts, stadium_opts, reset_params, current_team)
    elif "streaks" in active:
        show_streaks_interface(client, sql_template, team_opts, reset_params, current_team, stadium_opts)
    elif "heavy_losses" in active:
        show_heavy_losses_interface(client, sql_template, team_opts, current_team)
else:
    st.error("לא ניתן להתחבר לבסיס הנתונים. וודא שהגדרת את ה-Secrets ב-Streamlit Cloud.")
