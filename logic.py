import streamlit as st
import pandas as pd

def apply_custom_style():
    """ביטול RTL מבני ושימוש ביישור טקסט לימין למניעת שיבושים בסליידרים"""
    st.markdown("""
        <style>
        /* הגדרה כללית - האפליקציה נשארת LTR מבחינה מבנית כדי לא לשבור רכיבים */
        .main, div[data-testid="stSidebar"] {
            text-align: right;
        }

        /* יישור כותרות ותוויות לימין */
        h1, h2, h3, h4, h5, h6, label, p, .stMarkdown {
            text-align: right !important;
            direction: rtl !important;
        }

        /* תיקון ספציפי לסיידבר - יישור התוכן לימין */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            text-align: right;
            direction: rtl;
        }

        /* ביטול כל כפייה של RTL על הסליידר עצמו כדי שלא יתהפך וישבר */
        div[data-testid="stSlider"] {
            direction: ltr !important;
        }

        /* יישור הטבלאות לימין */
        [data-testid="stDataFrame"] {
            direction: rtl !important;
        }

        /* כפתורים אפורים נייטרליים (כמו שביקשת) */
        .stButton>button { 
            width: 100%; border-radius: 5px; 
            background-color: #F8F9FA !important; color: #495057 !important;
            border: 1px solid #CED4DA !important;
            transition: 0.2s;
        }
        
        .stButton>button:hover {
            background-color: #E2E6EA !important;
            border-color: #ADB5BD !important;
            color: #212529 !important;
        }

        /* הודעות מערכת בכחול בהיר */
        div[data-testid="stNotification"] { 
            background-color: #E8F0FE !important; 
            color: #1967D2 !important; 
            border: 1px solid #D2E3FC !important;
            text-align: right;
            direction: rtl;
        }

        /* צבע כחול לסליידר ולתגיות */
        .stSlider [data-baseweb="slider"] > div > div {
            background-color: #4482eb !important;
        }
        span[data-baseweb="tag"] {
            background-color: #4482eb !important;
            direction: rtl;
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
        
    if active: 
        st.session_state.active_query = active
    if selected:
        st.session_state.selected_mode = selected
        
    st.session_state.custom_conditions = []
    st.rerun()
