import streamlit as st
import pandas as pd

def show_streaks_interface(client, sql_template, reset_params):
    st.markdown("""
        <style>
            [data-testid="stPopover"] svg { display: none !important; }
            [data-testid="stPopover"] button { border: none !important; background: transparent !important; padding: 0px !important; color: #555 !important; font-size: 20px !important; }
            .cell-content { text-align: center; font-size: 16px; white-space: nowrap; width: 100%; font-weight: 500; }
            .header-content { text-align: center; color: #888; font-size: 13px; border-bottom: 1px solid #eee; padding-bottom: 4px; width: 100%; }
            [data-testid="stHorizontalBlock"] { direction: rtl; gap: 0px !important; }
            div[data-testid="stVerticalBlock"] > div { padding-top: 0px !important; padding-bottom: 0px !important; }
            .row-wrap { width: 100%; padding: 8px 0px; border-bottom: 1px solid #f0f0f0; display: block; }
            .summary-box { background-color: #f8f9fb; border-radius: 8px; padding: 12px; margin-bottom: 15px; display: flex; flex-direction: row; justify-content: space-around; border: 1px solid #eef0f2; direction: rtl; }
            .summary-item { display: flex; flex-direction: column; align-items: center; }
            .summary-label { font-size: 12px; color: #888; margin-bottom: 4px; }
            .summary-value { font-size: 16px; font-weight: bold; color: #222; }
        </style>
    """, unsafe_allow_html=True)

    if "streak_conditions" not in st.session_state:
        st.session_state.streak_conditions = []

    def format_duration(start, end):
        diff = pd.to_datetime(end) - pd.to_datetime(start)
        y, r = divmod(diff.days, 365)
        m, _ = divmod(r, 30)
        p = []
        if y > 0: p.append(f"{y} שנ'")
        if m > 0: p.append(f"{m} חו'")
        if not y and not m: p.append(f"{diff.days} ימים")
        return " ".join(p) if p else "יום אחד"

    # --- פילטרים ---
    with st.expander("🌍 הגדרות מסגרת", expanded=False):
        c1, c2 = st.columns([2, 1])
        with c1: comps = st.multiselect("מפעלים", [10, 11, 1, 2], default=[10], format_func=lambda x: {10:"ליגת העל", 11:"גביע", 1:"אירופה", 2:"נבחרת"}[x])
        with c2: loc = st.radio("מיקום", ["הכל", "בית", "חוץ"], horizontal=True)
        ct, ca = st.columns([3, 1])
        with ct: selected_teams = st.multiselect("סינון לפי קבוצות (אופציונלי):", options=[]) # כאן תבוא רשימת הקבוצות
        with ca: st.write(""); show_active = st.checkbox("פעילים בלבד", value=False)
        st.divider()
        cs, cml, clv = st.columns([2, 1, 1])
        with cs: scope = st.radio("טווח הרצף", ["כל הזמנים", "עונה בודדת", "מתחילת עונה"], horizontal=True)
        with cml: min_len = st.number_input("אורך רצף:", value=2, min_value=1)
        with clv: limit_val = st.selectbox("הגבלה:", [20, 50, 100, 200, 500], index=1)

    # --- לוגיקת חיפוש (תמציתית) ---
    if st.button("🚀 הרץ חיפוש", type="primary", use_container_width=True):
        # בניית הלוגיקה וקריאה ל-BigQuery (כפי שהיה לנו בגרסאות הקודמות)
        pass

    # --- תצוגת תוצאות ---
    if "last_results" in st.session_state and st.session_state.last_results is not None:
        res_df = st.session_state.last_results
        st.markdown("---")
        outer_cols = st.columns([0.3, 9.4, 0.3])
        with outer_cols[1]:
            inner_ratios = [0.4, 2.2, 0.7, 1.2, 1.8, 0.4]
            for idx, row in res_df.iterrows():
                with st.container():
                    st.markdown('<div class="row-wrap">', unsafe_allow_html=True)
                    r_cols = st.columns(inner_ratios)
                    r_cols[0].markdown(f"<div class='cell-content'>{idx + 1}</div>", unsafe_allow_html=True)
                    r_cols[1].markdown(f"<div class='cell-content'>{row['קבוצה']}</div>", unsafe_allow_html=True)
                    r_cols[2].markdown(f"<div class='cell-content'><b>{row['רצף']}</b>{' ✅' if row['פעיל'] == '✅' else ''}</div>", unsafe_allow_html=True)
                    r_cols[3].markdown(f"<div class='cell-content'>{row['עונות']}</div>", unsafe_allow_html=True)
                    r_cols[4].markdown(f"<div class='cell-content' style='color:#666;'>{format_duration(row['start_date'], row['end_date'])}</div>", unsafe_allow_html=True)
                    with r_cols[5].popover("⌄"):
                        m_list = row['streak_matches']
                        w = sum(1 for m in m_list if str(m.get('res')).upper() == 'W')
                        d = sum(1 for m in m_list if str(m.get('res')).upper() == 'D')
                        l = sum(1 for m in m_list if str(m.get('res')).upper() == 'L')
                        gf = sum(int(m.get('gf', 0)) for m in m_list)
                        ga = sum(int(m.get('ga', 0)) for m in m_list)
                        st.markdown(f"""
                        <div class="summary-box">
                            <div class="summary-item"><span class="summary-label">משחקים</span><span class="summary-value">{len(m_list)}</span></div>
                            <div class="summary-item"><span class="summary-label">ניצחונות</span><span class="summary-value">{w}</span></div>
                            <div class="summary-item"><span class="summary-label">תיקו</span><span class="summary-value">{d}</span></div>
                            <div class="summary-item"><span class="summary-label">הפסדים</span><span class="summary-value">{l}</span></div>
                            <div class="summary-item"><span class="summary-label">שערים</span><span class="summary-value">{ga}-{gf}</span></div>
                        </div>""", unsafe_allow_html=True)
                        # כאן תבוא טבלת הפירוט ה-HTML...
                    st.markdown('</div>', unsafe_allow_html=True)
