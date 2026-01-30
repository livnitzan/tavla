import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    with st.container():
        st.subheader("🔒 כניסת מנהל")
        pwd = st.text_input("הזן סיסמה:", type="password", key="admin_pwd_main")
        if st.button("התחבר"):
            if pwd == "1234":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("סיסמה שגויה")
        return False

def show_admin_interface(client):
    if not check_password():
        st.stop()

    st.title("🛠️ ממשק ניהול נתונים")

    today = datetime.now().date()
    start_range = today - timedelta(days=3)
    end_range = today + timedelta(days=3)
    goal_type_options = {"": "NULL", "נגיחה": "1", "פנדל": "2", "חופשית": "3", "קרן": "4"}
    id_to_goal_type = {v: k for k, v in goal_type_options.items()}

    @st.cache_data(ttl=600)
    def load_metadata():
        # טעינת כל השופטים לתרגום שמות
        ref_query = "SELECT ref_id, CONCAT(fname, ' ', lname) as full_name FROM `tavla-440015.table.refs`"
        all_refs = client.query(ref_query).to_dataframe()
        
        # טעינת כל הקבוצות לתרגום שמות (מבטיח שחדרה וקבוצות עבר יופיעו)
        team_query = "SELECT team_id, team FROM `tavla-440015.table.teams`"
        all_teams = client.query(team_query).to_dataframe()
        
        return all_refs, all_teams

    all_refs, all_teams = load_metadata()
    team_id_to_name = dict(zip(all_teams['team_id'], all_teams['team']))
    team_name_to_id = dict(zip(all_teams['team'], all_teams['team_id']))
    ref_id_to_name = dict(zip(all_refs['ref_id'], all_refs['full_name']))
    ref_name_to_id = dict(zip(all_refs['full_name'], all_refs['ref_id']))

    # משחקים להזנה בטווח התאריכים
    query_range = f"""
        SELECT game_id, date, week, comp_id, hteam, ateam, TRIM(side) as side, ref_id, done 
        FROM `tavla-440015.table.lgames` 
        WHERE date BETWEEN '{start_range}' AND '{end_range}' 
        AND season = (SELECT MAX(season) FROM `tavla-440015.table.lgames`)
        ORDER BY date ASC
    """
    df_range = client.query(query_range).to_dataframe()
    df_range['home_team_name'] = df_range['hteam'].map(team_id_to_name).fillna(df_range['hteam'])
    df_range['away_team_name'] = df_range['ateam'].map(team_id_to_name).fillna(df_range['ateam'])

    tab1, tab2 = st.tabs(["🎮 עדכון משחקים", "⚽ ניהול שערים"])

    with tab1:
        target_table = st.selectbox("בחר טבלה לעריכה:", ["lgames", "cgames", "games", "igames"], key="target_table_sel")
        if not df_range.empty:
            df_range['ref_name'] = df_range['ref_id'].map(ref_id_to_name).fillna("לא נבחר")
            edited_games = st.data_editor(df_range, column_config={
                "game_id": st.column_config.NumberColumn("ID", disabled=True),
                "side": st.column_config.SelectboxColumn("Side", options=["s", "n", "e", "w", ""]),
                "ref_name": st.column_config.SelectboxColumn("שופט", options=["לא נבחר"] + all_refs['full_name'].tolist()),
            }, hide_index=True, column_order=("game_id", "date", "week", "home_team_name", "away_team_name", "side", "ref_name", "done"), key=f"editor_{target_table}")
            
            if st.button(f"שמור שינויים ב-{target_table}", key="save_games_btn"):
                for i, row in edited_games.iterrows():
                    if not row.equals(df_range.iloc[i]):
                        ref_val = "NULL" if row['ref_name'] == "לא נבחר" else int(ref_name_to_id.get(row['ref_name'], 0))
                        update_sql = f"UPDATE `tavla-440015.table.{target_table}` SET side='{row['side']}', ref_id={ref_val}, done={bool(row['done'])} WHERE game_id={int(row['game_id'])}"
                        client.query(update_sql).result()
                st.success("הנתונים עודכנו!"); st.cache_data.clear(); st.rerun()

    with tab2:
        st.subheader("➕ הזנת שערים מרוכזת")
        if not df_range.empty:
            df_range['display'] = df_range.apply(lambda x: f"מחזור {x['week']} | {x['date']} | {x['home_team_name']} - {x['away_team_name']} (ID: {x['game_id']})", axis=1)
            sel_game = st.selectbox("בחר משחק להזנה:", options=df_range['display'].tolist(), key="sel_game_goals")
            game_row = df_range[df_range['display'] == sel_game].iloc[0]

            if 'temp_goals' not in st.session_state or st.session_state.get('last_game_id') != game_row['game_id']:
                st.session_state.temp_goals = []; st.session_state.last_game_id = game_row['game_id']; st.session_state.next_gorder = 1

            current_max_min = 90 if game_row['comp_id'] == 10 else 120

            with st.container(border=True):
                c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.5, 0.8, 0.8, 1.2, 1.5])
                with c1: in_team = st.selectbox("קבוצה", [game_row['home_team_name'], game_row['away_team_name']])
                with c2: in_scorer = st.text_input("כובש", key="in_scorer_input")
                is_technical = in_scorer.strip() == "טכני"
                is_og = in_scorer.strip() == "עצמי"
                with c3: in_min = st.number_input("דקה", min_value=0, max_value=current_max_min, step=1, disabled=is_technical)
                stoppage_allowed = in_min in [45, 90, 105, 120] and not is_technical
                with c4: in_stop = st.number_input("תוספת", min_value=0, step=1, disabled=not stoppage_allowed)
                with c5: in_type = st.selectbox("סוג", list(goal_type_options.keys()), disabled=is_technical or is_og)
                with c6: in_og_val = st.text_input("כובש העצמי", disabled=not is_og or is_technical)
                
                if st.button("➕ הוסף שורה לרשימה", use_container_width=True, key="add_row_btn"):
                    st.session_state.temp_goals.append({
                        "gorder": st.session_state.next_gorder, "team": in_team, "scorrer": in_scorer,
                        "minute": in_min if not is_technical else 0, "stoppage": in_stop if stoppage_allowed else 0, 
                        "type": in_type if (not is_technical and not is_og) else "", "ogscorrer": in_og_val if is_og else ""
                    })
                    st.session_state.next_gorder += 1; st.rerun()

            if st.session_state.temp_goals:
                st.info("שערים להזנה:")
                for idx, g in enumerate(st.session_state.temp_goals):
                    cols = st.columns([0.5, 2, 2, 1, 1, 1, 1, 1])
                    cols[0].write(f"#{g['gorder']}")
                    cols[1].write(f"קבוצה: {g['team']}")
                    cols[2].write(f"כובש: {g['scorrer']}")
                    if cols[7].button("🗑️", key=f"del_temp_{idx}_{g['gorder']}"):
                        st.session_state.temp_goals.pop(idx); st.rerun()
                
                if st.button("💾 שמור הכל ל-BigQuery", use_container_width=True, key="save_bulk_btn"):
                    for g in st.session_state.temp_goals:
                        og_sql = f"'{g['ogscorrer'].strip()}'" if g['ogscorrer'].strip() else "NULL"
                        insert_sql = f"INSERT INTO `tavla-440015.table.goals` (game_id, gorder, steam, scorrer, minute, stoppage, type, ogscorrer) VALUES ({int(game_row['game_id'])}, {int(g['gorder'])}, {int(team_name_to_id[g['team']])}, '{g['scorrer']}', {g['minute'] if g['minute']>0 else 'NULL'}, {g['stoppage'] if g['stoppage']>0 else 'NULL'}, {goal_type_options[g['type']]}, {og_sql})"
                        client.query(insert_sql).result()
                    st.success("נשמרו!"); st.session_state.temp_goals = []; st.session_state.next_gorder = 1; st.cache_data.clear(); st.rerun()

        st.divider()
        st.subheader("📝 עריכת שערים קיימים")
        
        # פילטרים לחיפוש עם מפתחות ייחודיים
        f_col1, f_col2, f_col3, f_col4, f_col5, f_col6 = st.columns(6)
        with f_col1: s_season = st.text_input("עונה", key="f_season")
        with f_col2: s_week = st.text_input("מחזור", key="f_week")
        with f_col3: s_game_id = st.text_input("קוד משחק", key="f_gid")
        with f_col4: s_date = st.date_input("תאריך", value=None, key="f_date")
        with f_col5: s_team = st.text_input("קבוצה", key="f_team")
        with f_col6: s_scorer = st.text_input("כובש", key="f_scorer")

        has_search = any([s_season, s_game_id, s_week, s_date, s_team, s_scorer])
        
        if has_search:
            where_clauses = ["1=1"]
            if s_season: where_clauses.append(f"m.season = {s_season}")
            if s_game_id: where_clauses.append(f"CAST(g.game_id AS STRING) LIKE '%{s_game_id}%'")
            if s_week: where_clauses.append(f"CAST(m.week AS STRING) = '{s_week}'")
            if s_date: where_clauses.append(f"m.date = '{s_date}'")
            if s_team: where_clauses.append(f"t.team LIKE '%{s_team}%'")
            if s_scorer: where_clauses.append(f"g.scorrer LIKE '%{s_scorer}%'")
            
            goals_query = f"""
                SELECT g.game_id, m.date, m.week, m.season, m.comp_id, g.gorder, g.steam, g.scorrer, g.minute, g.stoppage, CAST(g.type AS STRING) as type, g.ogscorrer 
                FROM `tavla-440015.table.goals` g 
                LEFT JOIN `tavla-440015.table.lgames` m ON g.game_id = m.game_id 
                LEFT JOIN `tavla-440015.table.teams` t ON g.steam = t.team_id
                WHERE {" AND ".join(where_clauses)}
                ORDER BY m.date DESC, g.game_id DESC, g.gorder ASC LIMIT 300
            """
        else:
            goals_query = f"""
                WITH current_season AS (SELECT MAX(season) as s FROM `tavla-440015.table.lgames`)
                SELECT g.game_id, m.date, m.week, m.season, m.comp_id, g.gorder, g.steam, g.scorrer, g.minute, g.stoppage, CAST(g.type AS STRING) as type, g.ogscorrer 
                FROM `tavla-440015.table.goals` g 
                LEFT JOIN `tavla-440015.table.lgames` m ON g.game_id = m.game_id 
                WHERE m.season = (SELECT s FROM current_season)
                AND m.week IN (
                    SELECT DISTINCT week 
                    FROM `tavla-440015.table.lgames` 
                    WHERE season = (SELECT s FROM current_season) AND date <= '{today}'
                    ORDER BY week DESC LIMIT 2
                )
                ORDER BY m.date DESC, g.game_id DESC, g.gorder ASC LIMIT 100
            """
        
        goals_df = client.query(goals_query).to_dataframe()
        goals_df['team_name'] = goals_df['steam'].map(team_id_to_name).fillna(goals_df['steam'])
        goals_df['type_label'] = goals_df['type'].apply(lambda x: id_to_goal_type.get(str(x).split('.')[0] if '.' in str(x) else str(x), ""))
        goals_df['מחיקה'] = False

        # עמודת game_id ראשונה בקצה
        edited_goals = st.data_editor(goals_df, column_config={
            "game_id": st.column_config.NumberColumn("ID", disabled=True),
            "date": st.column_config.DateColumn("תאריך", disabled=True),
            "season": st.column_config.NumberColumn("עונה", disabled=True),
            "team_name": st.column_config.SelectboxColumn("קבוצה", options=all_teams['team'].tolist()),
            "type_label": st.column_config.SelectboxColumn("סוג", options=list(goal_type_options.keys())),
            "מחיקה": st.column_config.CheckboxColumn("למחוק?")
        }, hide_index=True, column_order=("game_id", "date", "season", "week", "team_name", "gorder", "scorrer", "minute", "stoppage", "type_label", "ogscorrer", "מחיקה"), key="edit_goals_table")
        
        if st.button("💾 שמור שינויים / מחק שורות", key="save_edits_btn"):
            to_delete = edited_goals[edited_goals['מחיקה'] == True]
            if not to_delete.empty:
                if st.checkbox("אני מאשר מחיקה סופית", key="confirm_delete_checkbox"):
                    for _, row in to_delete.iterrows():
                        client.query(f"DELETE FROM `tavla-440015.table.goals` WHERE game_id={int(row['game_id'])} AND gorder={int(row['gorder'])}").result()
                    st.success("נמחק!"); st.cache_data.clear(); st.rerun()
            
            for i, row in edited_goals.iterrows():
                if not row.equals(goals_df.iloc[i]) and not row['מחיקה']:
                    curr_scorrer = str(row['scorrer']).strip()
                    final_type = "NULL" if (curr_scorrer in ["טכני", "עצמי"]) else goal_type_options[row['type_label']]
                    og_sql = f"'{str(row['ogscorrer']).strip()}'" if (str(row['ogscorrer']).strip() and str(row['ogscorrer']) != 'None' and curr_scorrer == 'עצמי') else "NULL"
                    update_sql = f"UPDATE `tavla-440015.table.goals` SET gorder={int(row['gorder'])}, steam={int(team_name_to_id.get(row['team_name'], row['steam']))}, scorrer='{row['scorrer']}', minute={row['minute'] if row['minute']>0 else 'NULL'}, stoppage={row['stoppage'] if row['stoppage']>0 else 'NULL'}, type={final_type}, ogscorrer={og_sql} WHERE game_id={int(goals_df.iloc[i]['game_id'])} AND gorder={int(goals_df.iloc[i]['gorder'])}"
                    client.query(update_sql).result()
            st.success("השינויים נשמרו!"); st.cache_data.clear(); st.rerun()