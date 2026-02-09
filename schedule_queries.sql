with coaching_terms as (
    select team, coach, sdate,
           case when active then current_date('Asia/Jerusalem') else edate end as edate
    from `tavla-440015.table.cterms`
),
raw_games as (
    select  
        gms.*,
        cast(gms.team as string) as team_id_str,
        cast(gms.rival as string) as rival_id_str,
        t.team as team_name,
        o.team as opp_name,
        case when lower(gms.lctn) = 'h' then t.team else o.team end as home_team,
        case when lower(gms.lctn) = 'h' then o.team else t.team end as away_team,
        std.stadium as stadium_name,
        case 
            when lower(gms.lctn) = 'h' then concat(cast(gms.gf as string), ' - ', cast(gms.ga as string))
            else concat(cast(gms.ga as string), ' - ', cast(gms.gf as string))
        end as score,
        cast(ifnull(ttrms.coach, ttrmcb.coach) as string) as tcoach,
        cast(ifnull(otrms.coach, otrmcb.coach) as string) as ocoach,
        tcv.rk as t_rk,
        tcv.plf as t_plf,
        tcv.season_sum as t_sum,
        ocv.rk as o_rk,
        ocv.plf as o_plf,
        ocv.season_sum as o_sum,
        dct.3pt,
        dct.gd,
        -- הוספת עמודת הזמן
        cast(gms.time as string) as game_time
    from `tavla-440015.table.srtdgms` as gms
    join `tavla-440015.table.teams` t on gms.team = t.team_id
    join `tavla-440015.table.teams` o on gms.rival = o.team_id
    left join `tavla-440015.table.stads` std on gms.stad_id = std.stad_id
    left join `tavla-440015.table.tmszn2` tcv on gms.season = tcv.season and gms.team = tcv.team_id
    left join `tavla-440015.table.tmszn2` ocv on gms.season = ocv.season and gms.rival = ocv.team_id
    left join `tavla-440015.table.szndct` dct on gms.season = dct.season
    left join coaching_terms as ttrms on gms.team = ttrms.team and gms.date between ttrms.sdate and ttrms.edate
    left join `tavla-440015.table.cbckp` as ttrmcb on gms.team = ttrmcb.team and gms.game_id = ttrmcb.game_id
    left join coaching_terms as otrms on gms.rival = otrms.team and gms.date between otrms.sdate and otrms.edate
    left join `tavla-440015.table.cbckp` as otrmcb on gms.rival = otrmcb.team and gms.game_id = otrmcb.game_id
)
select * from raw_games
where 1=1