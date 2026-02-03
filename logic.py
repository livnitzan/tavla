import streamlit as st
import pandas as pd

def apply_custom_style():
    """תיקון סופי לתפריט צף ויישור לימין"""
    st.markdown("""
        <style>
        /* יישור לימין של התוכן המרכזי בלבד */
        [data-testid="stMain"] .block-container {
            direction: RTL;
            text-align: right;
        }

        /* יישור התוכן בתוך הסיידבר בלי לשבור את אנימציית הסגירה שלו */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            direction: RTL;
            text-align: right;
        }
        
        /* מניעת ציפה של טקסט כשהסיידבר סגור */
        [data-testid="stSidebar"] {
            overflow-x: hidden;
        }

        /* כפתורים אפורים נייטרליים (כמו במחשב שלך) */
        .stButton>button { 
            width: 100%; border-radius: 5px; 
            background-color: #F8F9FA !important; color: #495057 !important;
            border: 1px solid #CED4DA !important;
        }
        
        .stButton>button:hover {
            background-color: #E2E6EA !important;
            border-color: #ADB5BD !important;
        }

        /* הודעות מערכת בכחול בהיר תואם */
        div[data-testid="stNotification"] { 
            background-color: #E8F0FE !important; 
            color: #1967D2 !important; 
            border: 1px solid #D2E3FC !important;
        }

        /* צבע כחול לסליידרים ורכיבי בחירה */
        .stSlider [data-baseweb="slider"] > div > div {
            background-color: #4482eb !important;
        }
        
        span[data-baseweb="tag"] {
            background-color: #4482eb !important;
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
