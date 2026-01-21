import streamlit as st
import pandas as pd

def show_losses_interface(client, sql_template):
    st.title("📉 ניתוח תבוסות כבדות (Heavy Losses)")

    # CSS מותאם לתצוגת הפסדים ותבוסות
    st.markdown("""
        <style>
            [data-testid="stPopover"] svg { display: none !important; }
            [data-testid="stPopover"] button {
                border: none !important;
                background: transparent !important;
                padding: 0px !important;
                color: #d9534f !important; /* צבע אדום להפסדים */
                font-size: 20px !important;
                width: 100% !important;
            }
            .loss-cell { text-align: center; font-size: 16px; font-weight: 500; }
            .loss-header { text-align: center; color: #888; font-size: 13px; border-bottom: 1px solid #eee; }
            [data-testid="stHorizontalBlock"] { direction: rtl; }
            .loss-row-wrap { width: 100%; padding: 10px 0px; border-bottom: 1px solid #f0f0f0; display: block; }
            
            /* תיבת סיכום לתבוסות */
            .loss-summary-box {
                background-color: #fff5f5;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 15px;
                display: flex;
                justify-content: space-around;
                border: 1px solid #ffe3e3;
                direction: rtl;
            }
            .summary-v { font-size: 16px; font-weight: bold; color: #c00; }
        </style>
    """, unsafe_allow_html=True)

    # פילטרים ייעודיים לתבוסות
    with st.expander("🛠️ הגדרות חיפוש", expanded=True):
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            margin = st.slider("הפרש שערים מינימלי:", 3, 10, 4)
        with c2:
            min_ga = st.number_input("מינימום ספיגה:", 3, 15, 4)
        with c3:
            limit_val = st.selectbox("הגבלת תוצאות:", [20, 50, 100], index=1)

    if st.button("🚀 חפש תבוסות", type="primary", use_container_width=True):
        # החלפת הפרמטרים בשאילתה
        query = sql_template.replace("{margin}", str(margin)).replace("{min_ga}", str(min_ga)).replace("{limit}", str(limit_val))
        
        with st.spinner("מנתח תבוסות..."):
            df = client.query(query).to_dataframe()
            st.session_state.last_losses = df

    if "last_losses" in st.session_state and st.session_state.last_losses is not None:
        df = st.session_state.last_losses
        st.markdown("---")
        
        # כותרות הטבלה
        h_cols = st.columns([0.5, 2, 1, 1, 1, 0.5])
        headers = ["#", "קבוצה", "כמות תבוסות", "ממוצע ספיגה", "הפסד שיא", ""]
        for col, h in zip(h_cols, headers):
            col.markdown(f"<div class='loss-header'>{h}</div>", unsafe_allow_html=True)

        for idx, row in df.iterrows():
            with st.container():
                st.markdown('<div class="loss-row-wrap">', unsafe_allow_html=True)
                r_cols = st.columns([0.5, 2, 1, 1, 1, 0.5])
                
                r_cols[0].markdown(f"<div class='loss-cell'>{idx + 1}</div>", unsafe_allow_html=True)
                r_cols[1].markdown(f"<div class='loss-cell'>{row['קבוצה']}</div>", unsafe_allow_html=True)
                r_cols[2].markdown(f"<div class='loss-cell'>{row['כמות_תבוסות']}</div>", unsafe_allow_html=True)
                r_cols[3].markdown(f"<div class='loss-cell'>{row['ממוצע_ספיגה']:.2f}</div>", unsafe_allow_html=True)
                r_cols[4].markdown(f"<div class='loss-cell' style='color:#c00;'>{row['הפסד_שיא']}</div>", unsafe_allow_html=True)
                
                with r_cols[5].popover("⌄"):
                    st.subheader(f"🏟️ פירוט תבוסות: {row['קבוצה']}")
                    
                    # הצגת רשימת המשחקים הספציפיים שהיו תבוסות
                    m_list = row['loss_matches']
                    
                    st.markdown(f"""
                        <div class="loss-summary-box">
                            <div><small>סה"כ ספיגה</small><br><span class="summary-v">{sum(int(m['ga']) for m in m_list)}</span></div>
                            <div><small>הפרש שערים מצטבר</small><br><span class="summary-v">-{sum(int(m['ga'])-int(m['gf']) for m in m_list)}</span></div>
                        </div>
                    """, unsafe_allow_html=True)

                    # טבלת פירוט משחקים
                    d_html = '<div dir="rtl"><table style="width:100%; border-collapse: collapse; text-align: center; font-size: 13px;">'
                    d_html += '<thead style="background-color: #fff5f5;"><tr><th>תאריך</th><th>עונה</th><th>יריבה</th><th>תוצאה</th><th>📺</th></tr></thead><tbody>'
                    
                    for m in m_list:
                        vid = f'<a href="{m["hglts"]}" target="_blank">📺</a>' if m.get("hglts") and str(m["hglts"]).lower() != "none" else ""
                        d_html += f'<tr style="border-bottom: 1px solid #eee; padding:5px;"><td>{pd.to_datetime(m["date"]).strftime("%d/%m/%Y")}</td><td>{m["season"]}</td><td>{m["rival_name"]}</td><td style="color:#c00; font-weight:bold;">{m["ga"]}-{m["gf"]}</td><td>{vid}</td></tr>'
                    
                    st.markdown(d_html + "</tbody></table></div>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
