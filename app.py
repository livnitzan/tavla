import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import os
import glob

# ייבוא הממשקים והלוגיקה
from logic import apply_custom_style, reset_params
from tpscr_ui import show_tpscr_interface
from heavy_ui import show_heavy_losses_interface
from streaks_ui import show_streaks_interface
from league_table_ui import show_league_table_interface 

# 1. הגדרות דף - הלוגו מופיע רק כאן (באייקון הלשונית)
st.set_page_config(page_title="מערכת נתוני כדורגל", page_icon="logo.png", layout="wide")

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

team_opts, stadium_opts = get_filter_options()


st.markdown("""
    <style>
    /* ביטול השטח המת למעלה */
    .block-container {
        padding-top: 2rem !important;
    }

    /* הבלטת כפתור התפריט (החצים) במובייל */
    @media (max-width: 768px) {
        /* גורם לכפתור המקורי להיות כחול וגדול */
        button[data-testid="stSidebarCollapseIcon"] {
            background-color: #3b82f6 !important;
            color: white !important;
            border-radius: 8px !important;
            width: 40px !important;
            height: 40px !important;
            position: fixed !important;
            top: 10px !important;
            right: 10px !important;
            z-index: 99999;
        }
        button[data-testid="stSidebarCollapseIcon"] svg {
            fill: white !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- הגדרות Sidebar ---
with st.sidebar:
    # אין כאן st.image - הלוגו הוסר מהתפריט
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
    
    # העיצוב המקורי של כפתורי הרדיו שלך
    st.markdown(f"""
    <style>
    /* צמצום השטח המת העליון */
    .block-container {{
        padding-top: 1.5rem !important;
    }}
    
    /* עיצוב כפתור התפריט במובייל */
    @media (max-width: 768px) {{
        button[data-testid="stSidebarCollapseIcon"] {{
            background-color: #3b82f6 !important;
            color: white !important;
            border-radius: 50% !important;
            width: 48px !important;
            height: 48px !important;
            position: fixed !important;
            top: 15px !important;
            right: 15px !important;
            z-index: 99999 !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        
        button[data-testid="stSidebarCollapseIcon"] svg {{
            fill: white !important;
            width: 24px !important;
            height: 24px !important;
        }}

        /* הוספת המילה "תפריט" מתחת לכפתור */
        button[data-testid="stSidebarCollapseIcon"]::after {{
            content: "תפריט";
            position: absolute;
            bottom: -22px;
            right: 50%;
            transform: translateX(50%);
            font-size: 12px;
            color: #3b82f6;
            font-weight: bold;
            white-space: nowrap;
        }}
    }}
    </style>

    <script>
    /* הוספת לוגו לאייפון (Apple Touch Icon) */
    var link = document.createElement('link');
    link.rel = 'apple-touch-icon';
    link.href = 'logo.png';
    document.getElementsByTagName('head')[0].appendChild(link);
    </script>
""", unsafe_allow_html=True)

    sql_files = glob.glob("*.sql")
    query_names = {os.path.basename(f).replace('.sql', '').replace('_', ' ').title(): f for f in sql_files}
    
    if 'active_query' not in st.session_state:
        st.session_state.active_query = list(query_names.values())[0]

    selected_name = st.radio(
        "בחר מנוע ניתוח:", 
        list(query_names.keys()),
        index=list(query_names.values()).index(st.session_state.active_query)
    )
    st.session_state.active_query = query_names[selected_name]

# 4. ניתוב (Routing)
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
