with all_seasons_stats as (
    -- חישוב מאזנים לכל עונה בנפרד תוך התחשבות בחוקי הליגה
    select  
        gms.season as start_season,
        gms.season as end_season,
        t.team as team_name,
        count(gms.game_id) as games,
        countif(lower(gms.res) = 'w') as wins,
        countif(lower(gms.res) = 'd') as draws,
        countif(lower(gms.res) = 'l') as losses,
        sum(gms.gf) as goals_for,
        sum(gms.ga) as goals_against,
        -- חישוב הפרש/יחס שערים לפי עמודת gd ב-szndct
        (case when any_value(dct.gd) then sum(gms.gf) - sum(gms.ga) 
              else round(case when sum(gms.ga) = 0 then sum(gms.gf) else sum(gms.gf) / sum(gms.ga) end, 2) 
         end) as goal_diff,
        -- חישוב אחוז הצלחה לפי חוק 3 נקודות או 2 נקודות (עמודת 3pt)
        round(100 * (
            ((case when any_value(dct.3pt) then 3 else 2 end) * countif(lower(gms.res) = 'w')) + countif(lower(gms.res) = 'd')
        ) / ((case when any_value(dct.3pt) then 3 else 2 end) * count(gms.game_id)), 2) as success_pct,
        -- עמודות לסינון ב-UI
        any_value(tcv.plf) as plf,
        any_value(tcv.rk) as rk,
        any_value(tcv.season_sum) as season_sum,
        any_value(tcv.last_season) as last_season
    from `tavla-440015.table.srtdgms` gms
    join `tavla-440015.table.teams` t 
      on gms.team = t.team_id
    left join `tavla-440015.table.tmszn2` tcv
      on gms.season = tcv.season and gms.team = tcv.team_id
    left join `tavla-440015.table.szndct` dct
      on gms.season = dct.season
    where gms.comp_id = 10
      and (gms.forfeit is not true or gms.forfeit is null)
      and gms.week <= @target_week
      and (
          @venue_filter = 'כללי' 
          or (@venue_filter = 'בית' and lower(gms.lctn) = 'h')
          or (@venue_filter = 'חוץ' and lower(gms.lctn) = 'a')
      )
    group by 
        gms.season, 
        t.team
),

ranked_stats as (
    -- חישוב דירוגים ופרסנטילים כלליים
    select *,
        count(*) over(partition by team_name) as total_club_seasons,
        count(*) over() as total_observations
    from all_seasons_stats
),

target_team as (
    select * from ranked_stats 
    where team_name like @selected_team_name 
    and start_season >= @season_start and end_season <= @season_end
)

select 'הקבוצה שנבחרה' as status, * from target_team
union all
select 'שיא היסטורי' as status, * from (
    select * from ranked_stats 
    where exists (select 1 from target_team)
    order by success_pct desc, goal_diff desc 
    limit 1
)
order by success_pct desc