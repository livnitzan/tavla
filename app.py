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
st.set_page_config(page_title="מערכת נתוני כדורגל", page_icon="logo.png", layout="wide")
apply_custom_style()

# 2. חיבור ל-BigQuery
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "creds.json"
client = bigquery.Client()

# 3. פונקציות נתונים
@st.cache_data(ttl=3600)
def get_season_data():
    try:
        query = "SELECT season, MAX(week) as max_week FROM `tavla-440015.table.srtdgms` GROUP BY season ORDER BY season DESC"
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

# טעינת המילונים
team_opts, stadium_opts = get_filter_options()

# --- עיצוב CSS מינימלי למניעת שטח מת והבלטת תפריט מובייל ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    
    @media (max-width: 768px) {
        button[data-testid="stSidebarCollapseIcon"] {
            background-color: #3b82f6 !important;
            color: white !important;
            border-radius: 50% !important;
            width: 45px !important;
            height: 45px !important;
            position: fixed !important;
            top: 10px !important;
            right: 10px !important;
            z-index: 99999 !important;
        }
        button[data-testid="stSidebarCollapseIcon"] svg { fill: white !important; }
    }

    /* עיצוב כפתורי הרדיו ב-sidebar */
    div[data-testid="stSidebar"] div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 10px 15px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] [data-checked="true"] > div {
        font-weight: bold;
        color: #3b82f6;
    }
    </style>
""", unsafe_allow_html=True)

# --- לוגיקת בחירת קובץ ---
sql_files = glob.glob("*.sql")
query_names = {os.path.basename(f).replace('.sql', '').replace('_', ' ').title(): f for f in sql_files}

# הכרחת הטבלה להיפתח ראשונה
if 'active_query' not in st.session_state:
    if sql_files:
        table_file = next((f for f in sql_files if "league_table" in f), sql_files[0])
        st.session_state.active_query = table_file

# --- הגדרות Sidebar ---
with st.sidebar:
    st.header("🔍 הגדרות גלובליות ⚙️")
    
    team_names = sorted(list(team_opts.keys()))
    full_team_list = ["ללא"] + team_names
    
    default_ix = 0
    for i, name in enumerate(full_team_list):
        if name != "ללא" and team_opts.get(name) == 11:
            default_ix = i
            break

    current_team = st.selectbox("קבוצת ברירת מחדל:", options=full_team_list, index=default_ix)
    st.write("---")
    
    if query_names:
        selected_name = st.radio(
            "בחר מנוע ניתוח:", 
            list(query_names.keys()),
            index=list(query_names.values()).index(st.session_state.active_query)
        )
        st.session_state.active_query = query_names[selected_name]

# 4. ניתוב (Routing) לממשקים
if 'active_query' in st.session_state:
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
