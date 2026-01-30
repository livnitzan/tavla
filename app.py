import streamlit as st
from google.cloud import bigquery
import os
import glob
from admin_ui import show_admin_interface

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
if "gcp_service_account" in st.secrets:
    from google.oauth2 import service_account
    info = dict(st.secrets["gcp_service_account"])
    
    # תיקון חסין תקלות למפתח הפרטי
    raw_key = info["private_key"]
    if "\\n" in raw_key:
        info["private_key"] = raw_key.replace("\\n", "\n")
    
    credentials = service_account.Credentials.from_service_account_info(info)
    client = bigquery.Client(credentials=credentials, project=info["project_id"])
else:
    # הגדרת נתיב לקובץ מקומי במחשב
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "creds.json"
    client = bigquery.Client()

# 3. פונקציות נתונים
@st.cache_data(ttl=3600)
def get_season_data():
    try:
        query = "select season, max(week) as max_week from `tavla-440015.table.srtdgms` group by season order by season desc"
        df = client.query(query).to_dataframe()
        return df.set_index('season')['max_week'].to_dict()
    except:
        return {2026: 19}

@st.cache_data(ttl=3600)
def get_filter_options():
    if not client: return {}, {}
    try:
        query = """
            select distinct t.team, t.team_id,
                   max(case when m.season = 2026 and m.comp_id = 10 then 1 else 0 end) as is_league_2026
            from `tavla-440015.table.teams` t
            left join `tavla-440015.table.srtdgms` m on t.team_id = m.team or t.team_id = m.rival
            where t.team_id < 100
            group by t.team, t.team_id
        """
        df = client.query(query).to_dataframe()
        
        all_teams = dict(zip(df['team_id'], df['team']))
        league_2026_ids = set(df[df['is_league_2026'] == 1]['team_id'])
        vip_ids = [11, 12, 17, 25, 36]
        final_team_dict = {}

        for t_id in vip_ids:
            if t_id in all_teams:
                final_team_dict[all_teams[t_id]] = t_id

        other_league_teams = []
        for t_id in league_2026_ids:
            if t_id not in vip_ids and t_id in all_teams:
                other_league_teams.append(all_teams[t_id])
        
        for name in sorted(other_league_teams):
            t_id = [k for k, v in all_teams.items() if v == name][0]
            final_team_dict[name] = t_id

        remaining_names = []
        for t_id, name in all_teams.items():
            if name not in final_team_dict:
                remaining_names.append(name)
        
        for name in sorted(remaining_names):
            t_id = [k for k, v in all_teams.items() if v == name][0]
            final_team_dict[name] = t_id

        s_df = client.query("select stad_id, stadium from `tavla-440015.table.stads` order by stadium").to_dataframe()
        stadium_dict = dict(zip(s_df['stadium'], s_df['stad_id']))
        
        return final_team_dict, stadium_dict
    except Exception as e:
        st.error(f"Error: {e}")
        return {}, {}

team_opts, stadium_opts = get_filter_options()

# --- הגדרות Sidebar ---
with st.sidebar:
    st.header("🔍 הגדרות גלובליות ⚙️")
    
    team_names = list(team_opts.keys())
    full_team_list = ["ללא"] + team_names
    current_team = st.selectbox("קבוצת ברירת מחדל:", options=full_team_list, index=0)
    
    st.write("---")
    
    sql_files = glob.glob("*.sql")
    query_names = {os.path.basename(f).replace('.sql', '').replace('_', ' ').title(): f for f in sql_files}
    
    analysis_options = list(query_names.keys())
    admin_option = "🔧 ניהול מערכת"
    full_options = analysis_options + [admin_option]
    
    if 'selected_mode' not in st.session_state:
        st.session_state.selected_mode = full_options[0]

    selected_name = st.radio(
        "בחר מנוע ניתוח:", 
        full_options, 
        index=full_options.index(st.session_state.selected_mode)
    )
    
    st.session_state.selected_mode = selected_name
    
    if selected_name in query_names:
        st.session_state.active_query = query_names[selected_name]
    else:
        st.session_state.active_query = "admin"

# 4. ניתוב (Routing)
if st.session_state.selected_mode == "🔧 ניהול מערכת":
    show_admin_interface(client)
else:
    active = st.session_state.active_query
    
    if active and active != "admin":
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