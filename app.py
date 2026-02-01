import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import os
import glob
import json
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

# 2. חיבור ל-BigQuery (מותאם לענן)
if "gcp_service_account" in st.secrets:
    info = dict(st.secrets["gcp_service_account"])
    # התיקון הקריטי למפתח
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    credentials = service_account.Credentials.from_service_account_info(info)
    client = bigquery.Client(credentials=credentials, project=info["project_id"])
else:
    st.error("לא נמצאו הגדרות חיבור ב-Secrets")
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
    if not client: return {}, {}
    try:
        # שאילתה שבודקת גם מי בליגת העל העונה
        query = """
            SELECT DISTINCT t.team, t.team_id,
                   MAX(CASE WHEN m.season = 2026 AND m.comp_id = 10 THEN 1 ELSE 0 END) as is_league_2026
            FROM `tavla-440015.table.teams` t
            LEFT JOIN `tavla-440015.table.srtdgms` m ON t.team_id = m.team OR t.team_id = m.rival
            WHERE t.team_id < 100
            GROUP BY t.team, t.team_id
        """
        df = client.query(query).to_dataframe()
        
        # מילון עזר
        all_teams = dict(zip(df['team_id'], df['team']))
        league_2026_ids = set(df[df['is_league_2026'] == 1]['team_id'])

        # 1. הגדרת חמש הגדולות (VIP)
        vip_ids = [11, 12, 17, 25, 36]
        
        final_team_dict = {}

        # א. הוספת ה-VIP לפי הסדר שנתת
        for t_id in vip_ids:
            if t_id in all_teams:
                final_team_dict[all_teams[t_id]] = t_id

        # ב. הוספת יתר קבוצות ליגת העל 2026 (אלפביתית)
        other_league_teams = []
        for t_id in league_2026_ids:
            if t_id not in vip_ids and t_id in all_teams:
                other_league_teams.append(all_teams[t_id])
        
        for name in sorted(other_league_teams):
            final_team_dict[name] = all_teams.get(next(k for k, v in all_teams.items() if v == name), 0) # תיקון קטן למשיכת ה-ID
            # דרך פשוטה יותר למשיכת ה-ID:
            t_id = [k for k, v in all_teams.items() if v == name][0]
            final_team_dict[name] = t_id

        # ג. הוספת כל השאר (אלפביתית)
        remaining_names = []
        for t_id, name in all_teams.items():
            if name not in final_team_dict:
                remaining_names.append(name)
        
        for name in sorted(remaining_names):
            t_id = [k for k, v in all_teams.items() if v == name][0]
            final_team_dict[name] = t_id

        # אצטדיונים
        s_df = client.query("SELECT stad_id, stadium FROM `tavla-440015.table.stads` ORDER BY stadium").to_dataframe()
        stadium_dict = dict(zip(s_df['stadium'], s_df['stad_id']))
        
        return final_team_dict, stadium_dict
    except Exception as e:
        st.error(f"Error: {e}")
        return {}, {}

# טעינת הנתונים
team_opts, stadium_opts = get_filter_options()

# --- הגדרות Sidebar ---
with st.sidebar:
    st.header("🔍 הגדרות גלובליות ⚙️")
    
    # 1. בחירת קבוצת ברירת מחדל
    team_names = list(team_opts.keys())
    full_team_list = ["ללא"] + team_names
    current_team = st.selectbox("קבוצת ברירת מחדל:", options=full_team_list, index=0)
    
    st.write("---")
    
    # 2. הכנת רשימת מנועי הניתוח מקבצי ה-SQL
    sql_files = glob.glob("*.sql")
    query_names = {os.path.basename(f).replace('.sql', '').replace('_', ' ').title(): f for f in sql_files}
    
    # 3. הוספת אופציית הניהול לרשימה
    analysis_options = list(query_names.keys())
    admin_option = "🔧 ניהול מערכת"
    full_options = analysis_options + [admin_option]
    
    # הגדרת ברירת מחדל ראשונית אם עדיין אין
    if 'selected_mode' not in st.session_state:
        st.session_state.selected_mode = full_options[0]

    # 4. רכיב הבחירה (Radio)
    selected_name = st.radio(
        "בחר מנוע ניתוח:", 
        full_options, 
        index=full_options.index(st.session_state.selected_mode)
    )
    
    # עדכון ה-session_state
    st.session_state.selected_mode = selected_name
    
    # אם נבחר מנוע ניתוח (קובץ SQL), נעדכן את ה-active_query
    if selected_name in query_names:
        st.session_state.active_query = query_names[selected_name]
    else:
        # במצב ניהול, אנחנו לא צריכים קובץ SQL פעיל
        st.session_state.active_query = "admin"

# 4. ניתוב (Routing)
if st.session_state.selected_mode == "🔧 ניהול מערכת":
    show_admin_interface(client)
else:
    active = st.session_state.active_query
    
    # וידוא שיש קובץ פעיל לפני פתיחה
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
