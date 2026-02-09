import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

def show_ltgraph_interface(client, get_season_data):
    st.markdown("<h1 style='text-align: center; font-weight: 400; color: #2c3e50; font-family: sans-serif; margin-bottom: 25px;'>מגמת מיקומים</h1>", unsafe_allow_html=True)
    
    season_dict = get_season_data()
    season_options = sorted(list(season_dict.keys()), reverse=True)

    # הגדרת הצבעים המזוהים
    color_map = {
        "מכבי ת\"א": "#FFD700", "מכבי נתניה": "#FFD700", "בית\"ר ירושלים": "#FFD700",
        "מכבי חיפה": "#2ecc71", "הפועל ת\"א": "#e74c3c", "הפועל חיפה": "#e74c3c",
        "הפועל ב\"ש": "#e74c3c", "בני סכנין": "#e74c3c", "הפועל ירושלים": "#e74c3c",
        "מ.ס. אשדוד": "#FF8C00", "הפועל פ\"ת": "#87CEEB", "עירוני ק\"ש": "#4169E1",
        "עירוני טבריה": "#000080", "מכבי בני ריינה": "#D4AF37"
    }

    tab_single, tab_multi = st.tabs(["📊 מבט עונתי", "📈 רצף היסטורי"])

    # --- לשונית 1: מבט עונתי (הקוד המלא שהיה חסר) ---
    with tab_single:
        col_a, col_b = st.columns([1, 1])
        with col_a:
            s_season = st.selectbox("בחר עונה:", season_options, index=0, key="single_s_sel")
        with col_b:
            max_w = season_dict.get(s_season, 30)
            s_week = st.number_input("עד מחזור:", 1, max_w, max_w, key="single_w_sel")

        query_single = f"""
        WITH SeasonRules AS (SELECT * FROM `table.szndct` WHERE season = {s_season}),
        PrevRank AS (
            SELECT team as team_id, 
            RANK() OVER (ORDER BY SUM(CASE WHEN res = 'W' THEN 3 WHEN res = 'D' THEN 1 ELSE 0 END) DESC, SUM(gf-ga) DESC) as pr 
            FROM `table.srtdgms` WHERE season = {s_season}-1 AND comp_id=10 AND done IS TRUE GROUP BY team
        ),
        CumulativeStats AS (
            SELECT s.week, t.team as team_name, t.team_id,
            SUM(CASE WHEN s.res = 'W' THEN (SELECT CASE WHEN IFNULL(`3pt`, TRUE) THEN 3 ELSE 2 END FROM SeasonRules) WHEN s.res = 'D' AND s.forfeit IS NOT TRUE THEN 1 ELSE 0 END) OVER (PARTITION BY t.team_id ORDER BY s.week) as pts,
            SUM(s.gf-s.ga) OVER (PARTITION BY t.team_id ORDER BY s.week) as gd,
            SUM(s.gf) OVER (PARTITION BY t.team_id ORDER BY s.week) as gf,
            s.date
            FROM `table.srtdgms` s JOIN `table.teams` t ON s.team = t.team_id
            WHERE s.season = {s_season} AND s.comp_id = 10 AND s.week > 0 AND s.week <= {s_week} AND s.done IS TRUE
        ),
        RankCalc AS (
            SELECT cs.*,
            (cs.pts - COALESCE((SELECT SUM(pts) FROM `table.ddctn` d WHERE d.team = cs.team_id AND d.date <= cs.date AND d.season={s_season}), 0)) as final_pts,
            COALESCE((SELECT pr FROM PrevRank WHERE team_id=cs.team_id), 99) as prev_season_rank
            FROM CumulativeStats cs
        )
        SELECT week, team_name, 
        RANK() OVER (PARTITION BY week ORDER BY final_pts DESC, gd DESC, gf DESC, prev_season_rank ASC) as rank
        FROM RankCalc ORDER BY week, rank
        """
        try:
            df_s = client.query(query_single).to_dataframe()
            if not df_s.empty:
                num_t = df_s['team_name'].nunique()
                fig_s = px.line(df_s, x="week", y="rank", color="team_name", markers=True, color_discrete_map=color_map, template="simple_white")
                fig_s.update_yaxes(range=[num_t + 0.5, 0.5], tick0=1, dtick=1, title="מיקום", gridcolor='#f1f1f1', griddash='dot')
                fig_s.update_xaxes(range=[0.8, s_week + 0.2], tick0=1, dtick=1, title="מחזור")
                fig_s.update_layout(height=600, hovermode="x unified", legend=dict(orientation="h", y=-0.2), uirevision=str(s_season))
                st.plotly_chart(fig_s, use_container_width=True)
            else:
                st.warning("לא נמצאו נתונים לעונה זו.")
        except Exception as e:
            st.error(f"שגיאה בלשונית עונתית: {e}")

    # --- לשונית 2: רצף היסטורי ---
    with tab_multi:
        col_c, col_d = st.columns(2)
        with col_c:
            start_s = st.selectbox("מעונה:", sorted(season_options), index=0)
        with col_d:
            end_s = st.selectbox("עד עונה:", sorted(season_options), index=len(season_options)-1)

        query_multi = f"""
        WITH BaseStats AS (
            SELECT 
                s.season, s.week, t.team as team_name, t.team_id,
                DENSE_RANK() OVER (ORDER BY s.season, s.week) as timeline_index,
                SUM(CASE WHEN s.res='W' THEN 3 WHEN s.res='D' THEN 1 ELSE 0 END) OVER (PARTITION BY s.season, t.team_id ORDER BY s.week) as pts_cum,
                SUM(s.gf-s.ga) OVER (PARTITION BY s.season, t.team_id ORDER BY s.week) as gd_cum,
                SUM(s.gf) OVER (PARTITION BY t.team_id ORDER BY s.season, s.week) as gf_cum
            FROM `table.srtdgms` s 
            JOIN `table.teams` t ON s.team = t.team_id
            WHERE s.season BETWEEN {start_s} AND {end_s} AND s.comp_id = 10 AND s.week > 0 AND s.done IS TRUE
        )
        SELECT season, week, team_name, timeline_index,
        RANK() OVER (PARTITION BY season, week ORDER BY pts_cum DESC, gd_cum DESC, gf_cum DESC) as rank
        FROM BaseStats
        """
        try:
            df_m = client.query(query_multi).to_dataframe()
            if not df_m.empty:
                teams = sorted(df_m['team_name'].unique())
                teams_selected = st.multiselect("בחר קבוצות:", teams, default=["מכבי חיפה", "מכבי ת\"א"], key="multi_t_sel")
                
                # יצירת נתקים בין עונות
                new_rows = []
                for team in teams_selected:
                    team_df = df_m[df_m['team_name'] == team]
                    for s in sorted(df_m['season'].unique())[:-1]:
                        if s in team_df['season'].values:
                            last_idx = team_df[team_df['season'] == s]['timeline_index'].max()
                            new_rows.append({'season': s, 'week': 99, 'team_name': team, 'timeline_index': last_idx + 0.5, 'rank': None})
                
                plot_df = pd.concat([df_m[df_m['team_name'].isin(teams_selected)], pd.DataFrame(new_rows)]).sort_values('timeline_index')

                fig_m = px.line(plot_df, x="timeline_index", y="rank", color="team_name", markers=False, color_discrete_map=color_map, template="simple_white")
                max_rank = int(df_m['rank'].max())
                fig_m.update_yaxes(range=[max_rank + 0.5, 0.5], tick0=1, dtick=1, title="מיקום", showgrid=False)

                # ציר X: שם עונה ואמצע
                tick_vals, tick_text = [], []
                for s in sorted(df_m['season'].unique()):
                    s_data = df_m[df_m['season'] == s]
                    tick_vals.append(s_data['timeline_index'].min())
                    tick_text.append(f"<b>{s}</b>")
                    mid_w = int(np.ceil(s_data['week'].max() / 2))
                    w_mid_idx = s_data[s_data['week'] == mid_w]['timeline_index'].max()
                    if not np.isnan(w_mid_idx):
                        tick_vals.append(w_mid_idx)
                        tick_text.append(f"{mid_w}")

                fig_m.update_xaxes(tickvals=tick_vals, ticktext=tick_text, title=None, showgrid=False)

                # גריד וקווים
                shapes = []
                season_bounds = df_m.groupby('season')['timeline_index'].agg(['min', 'max']).reset_index()
                for i in range(len(season_bounds) - 1):
                    x_pos = season_bounds.iloc[i]['max'] + 0.5
                    shapes.append(dict(type='line', x0=x_pos, x1=x_pos, y0=0.5, y1=max_rank + 0.5, line=dict(color="#7f8c8d", width=2, dash="dash")))
                for r in range(2, max_rank + 1, 2):
                    shapes.append(dict(type='line', x0=df_m['timeline_index'].min(), x1=df_m['timeline_index'].max(), y0=r, y1=r, line=dict(color="rgba(189, 195, 199, 0.3)", width=1), layer='below'))
                
                fig_m.update_layout(shapes=shapes, height=600, hovermode="x unified", legend=dict(orientation="h", y=-0.2), margin=dict(l=40, r=40, t=20, b=20))
                fig_m.update_traces(connectgaps=False, line=dict(width=3.5))
                st.plotly_chart(fig_m, use_container_width=True)

                # לוגיקת השוואה
                if len(teams_selected) == 2:
                    t1, t2 = teams_selected[0], teams_selected[1]
                    comp_df = df_m[df_m['team_name'].isin([t1, t2])].pivot(index='timeline_index', columns='team_name', values=['rank', 'season', 'week']).dropna()
                    if not comp_df.empty:
                        last_row = comp_df.iloc[-1]
                        r1, r2 = last_row[('rank', t1)], last_row[('rank', t2)]
                        lower_team = t1 if r1 > r2 else t2
                        upper_team = t2 if r1 > r2 else t1
                        past_leads = comp_df[comp_df[('rank', lower_team)] < comp_df[('rank', upper_team)]]
                        if not past_leads.empty:
                            l_season, l_week = int(past_leads.iloc[-1][('season', lower_team)]), int(past_leads.iloc[-1][('week', lower_team)])
                            st.info(f"הפעם האחרונה ש-**{lower_team}** הובילה בטבלה על **{upper_team}**: מחזור **{l_week}**, עונת **{l_season}**")
                        else:
                            st.warning(f"בטווח שנבחר, **{lower_team}** מעולם לא הובילה בטבלה על **{upper_team}**")
        except Exception as e:
            st.error(f"שגיאה בהיסטורי: {e}")