import streamlit as st
import pandas as pd

def apply_custom_style():
    """החזרת RTL לתוכן וטקסט תוך שמירה על יציבות רכיבי המערכת"""
    st.markdown("""
        <style>
        /* יישור לימין של גוף העמוד */
        .main .block-container {
            direction: RTL;
            text-align: right;
        }

        /* יישור טקסט, כותרות ותוויות */
        h1, h2, h3, h4, h5, h6, label, p, span, .stMarkdown {
            direction: RTL !important;
            text-align: right !important;
        }

        /* יישור הסיידבר לימין בלי לשבור את האנימציה שלו */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            direction: RTL;
            text-align: right;
        }

        /* --- תיקון סליידר: מראה נקי כמו במחשב --- */
        /* השארת המבנה ב-LTR כדי שהחישובים והצבעים לא יתבלבלו */
        div[data-testid="stSlider"] {
            direction: LTR !important;
        }
        
        /* צביעת הטווח הנבחר בלבד בכחול הבהיר */
        div[data-testid="stSlider"] [data-baseweb="slider"] > div {
            background-color: transparent !important;
        }
        div[data-testid="stSlider"] [data-baseweb="slider"] div[style*="left"] {
            background-color: #4482eb !important;
        }

        /* כפתורים אפורים נייטרליים */
        .stButton>button { 
            width: 100%; border-radius: 5px; 
            background-color: #F8F9FA !important; color: #495057 !important;
            border: 1px solid #CED4DA !important;
        }
        
        .stButton>button:hover {
            background-color: #E2E6EA !important;
            border-color: #ADB5BD !important;
        }

        /* הודעות מערכת בכחול בהיר */
        div[data-testid="stNotification"] { 
            background-color: #E8F0FE !important; 
            color: #1967D2 !important; 
            border: 1px solid #D2E3FC !important;
            direction: RTL;
            text-align: right;
        }

        /* צבע לתגיות בחירה (כמו 'ליגת העל') */
        span[data-baseweb="tag"] {
            background-color: #4482eb !important;
            direction: RTL;
        }
        
        /* יישור טבלאות לימין */
        [data-testid="stDataFrame"] {
            direction: RTL !important;
        }
        </style>
        """, unsafe_allow_html=True)

def reset_params():
    """איפוס פרמטרים וחזרה למצב נקי"""
    active = st.session_state.get('active_query')
    selected = st.session_state.get('selected_mode')
    for key in list(st.session_state.keys()):
        if not key.startswith('_'):
            del st.session_state[key]
    if active: st.session_state.active_query = active
    if selected: st.session_state.selected_mode = selected
    st.session_state.custom_conditions = []
    st.rerun()
