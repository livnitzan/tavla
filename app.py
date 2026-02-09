import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import os
import glob
import json

# ייבוא הממשקים מהקבצים השונים
from admin_ui import show_admin_interface
from logic import apply_custom_style, reset_params
from tpscr_ui import show_tpscr_interface
from heavy_ui import show_heavy_losses_interface
from streaks_ui import show_streaks_interface
from league_table_ui import show_league_table_interface
from crowd_ui import show_crowd_interface
from ltgraph_ui import show_ltgraph_interface
from ai_logic import show_ai_query_interface
from comparison_ui import show_comparison_ui
from schedule_ui import show_schedule_ui

# 1. הגדרות דף
st.set_page_config(page_title="מערכת נתוני כדורגל", page_icon="logo.png", layout="wide")
apply_custom_style()

# 2. חיבור ל-BigQuery (הלוגיקה המקורית מהגיטהאב - לא נגעתי)
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

if not client:
    st.error("לא נמצאו הגדרות חיבור ל-BigQuery. וודא שקובץ ה-Secrets מוגדר בענן או creds.json קיים מקומית.")
    st.stop()

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
        # שליפת קבוצות עם לוגיקת ה-VIP והסדר מהגיטהאב
        query = """
            SELECT DISTINCT t.team, t.team_id,
                   MAX(CASE WHEN m.season = 2026 AND m.comp_id = 10 THEN 1 ELSE 0 END) as is_league_2026
            FROM `tavla-440015.table.teams` t
            LEFT JOIN `tavla-440015.table.srtdgms` m ON t.team_id = m.team OR t.team_id = m.rival
            WHERE t.team_id < 100
            GROUP BY t.team, t.team_id
        """
        df = client.query(query).to_dataframe()
        all_teams = dict(zip(df['team_id'], df['team']))
        league_2026_ids = set(df[df['is_league_2026'] == 1]['team_id'])
        
        vip_ids = [11, 12, 17, 25, 36]
        final_team_dict = {}
        for t_id in vip_ids:
            if t_id in all_teams: final_team_dict[all_teams[t_id]] = t_id
        
        other_league = sorted([all_teams[tid] for tid in league_2026_ids if tid not in vip_ids])
        for name in other_league:
            t_id = [k for k, v in all_teams.items() if v == name][0]
            final_team_dict[name] = t_id

        remaining = sorted([name for tid, name in all_teams.items() if name not in final_team_dict])
        for name in remaining:
            t_id = [k for k, v in all_teams.items() if v == name][0]
            final_team_dict[name] = t_id

        # אצטדיונים
        s_df = client.query("SELECT stad_id, stadium FROM `tavla-440015.table.stads` ORDER BY stadium").to_dataframe()
        stadium_dict = dict(zip(s_df['stadium'], s_df['stad_id']))

        # מאמנים (השליפה המורכבת מהמחשב)
        c_query = """
            SELECT coach_id,
                TRIM(CONCAT(COALESCE(fname, ''), ' ', COALESCE(lname, ''), 
                CASE WHEN nname IS NOT NULL THEN CONCAT(' (', nname, ')') ELSE '' END)) as coach_name
            FROM `tavla-440015.table.coaches` ORDER BY coach_name
        """
        c_df = client.query(c_query).to_dataframe()
        coach_dict = dict(zip(c_df['coach_name'], c_df['coach_id']))
        
        return final_team_dict, stadium_dict, coach_dict
    except Exception as e:
        st.error(f"Error fetching options: {e}")
        return {}, {}, {}

team_opts, stadium_opts, coach_opts = get_filter_options()
season_dict = get_season_data()

# --- הגדרות Sidebar ---
with st.sidebar:
    st.header("🔍 הגדרות גלובליות ⚙️")
    team_names = list(team_opts.keys())
    full_team_list = ["ללא"] + team_names
    current_team = st.selectbox("קבוצת ברירת מחדל:", options=full_team_list, index=0)
    
    st.write("---")
    sql_files = glob.glob("*.sql")
    translation = {
        "league_table": "טבלת הליגה", "ltgraph": "גרף מיקומים", "streaks_query": "רצפים",
        "tpscr": "כובשים", "heavy_losses": "תוצאות", "crowd": "קהל",
        "comparison_queries": "השוואת מאזנים", "schedule_queries": "לוח משחקים ומאזנים"
    }

    query_names = {}
    for f in sql_files:
        base = os.path.basename(f).replace('.sql', '')
        display_name = translation.get(base, base.replace('_', ' ').title())
        query_names[display_name] = f
    
    full_options = list(query_names.keys()) + ["🤖 עוזר AI (ניסיוני)", "🔧 ניהול מערכת"]
    
    if 'selected_mode' not in st.session_state:
        st.session_state.selected_mode = "טבלת הליגה" if "טבלת הליגה" in full_options else full_options[0]

    selected_name = st.radio("בחר מנוע ניתוח:", full_options, index=full_options.index(st.session_state.selected_mode) if st.session_state.selected_mode in full_options else 0)
    st.session_state.selected_mode = selected_name

# 4. ניתוב (Routing) - הוספת הממשקים החדשים
if st.session_state.selected_mode == "🔧 ניהול מערכת":
    show_admin_interface(client)
elif st.session_state.selected_mode == "🤖 עוזר AI (ניסיוני)":
    show_ai_query_interface(client)
else:
    active_path = query_names.get(st.session_state.selected_mode)
    if active_path:
        if "schedule_queries" in active_path:
            show_schedule_ui(client, team_opts, stadium_opts, coach_opts)
        elif "comparison_queries" in active_path:
            show_comparison_ui(client)
        else:
            with open(active_path, 'r', encoding='utf-8-sig') as f:
                sql_template = f.read()
            
            if "league_table" in active_path:
                show_league_table_interface(client, sql_template, get_season_data, current_team)
            elif "ltgraph" in active_path:
                show_ltgraph_interface(client, get_season_data)
            elif "tpscr" in active_path:
                show_tpscr_interface(client, sql_template, get_season_data, team_opts, stadium_opts, reset_params, current_team)
            elif "streaks" in active_path:
                show_streaks_interface(client, sql_template, team_opts, reset_params, current_team, stadium_opts)
            elif "heavy_losses" in active_path:
                show_heavy_losses_interface(client, sql_template, team_opts, current_team)
            elif "crowd" in active_path:
                # אתחול משתני מצב לקהל כפי שמופיע בגיטהאב
                if 'df_weeks_current' not in st.session_state: st.session_state['df_weeks_current'] = None
                if 'weeks_show_all' not in st.session_state: st.session_state['weeks_show_all'] = False
                show_crowd_interface(client, sql_template, get_season_data, team_opts, stadium_opts, current_team)
