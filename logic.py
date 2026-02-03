import streamlit as st

def apply_custom_style():
    """החלת עיצוב CSS מנקודת המוצא עם דגשים כחולים במקום אדומים"""
    st.markdown("""
        <style>
        .main { direction: RTL; text-align: right; }
        [data-testid="stSidebar"] { direction: RTL; text-align: right; }
        
        /* RTL לכל האפליקציה */
        div.stApp { direction: RTL; }

        /* שינוי צבע לתוויות ותיבות בחירה */
        .stSelectbox label, .stMultiSelect label, .stRadio label {
            color: #0D47A1 !important;
            font-weight: 500;
        }

        /* כפתורים אפורים נייטרליים כמו במחשב */
        .stButton>button { 
            width: 100%; border-radius: 5px; 
            background-color: #F8F9FA !important; color: #495057 !important;
            border: 1px solid #CED4DA !important;
        }
        
        .stButton>button:hover {
            background-color: #E2E6EA !important;
            border-color: #ADB5BD !important;
        }

        /* הודעות מערכת בכחול */
        div[data-testid="stNotification"] { 
            background-color: #E3F2FD !important; 
            color: #0D47A1 !important; 
            border: 1px solid #BBDEFB !important;
        }

        /* צבע כחול לספינר (טעינה) */
        .stSpinner > div {
            border-top-color: #0D47A1 !important;
        }
        </style>
        """, unsafe_allow_html=True)

def reset_params():
    """איפוס פרמטרים וחזרה למצב נקי"""
    # שמירת נתיב השאילתה הפעילה כדי לא לצאת מהעמוד
    active = st.session_state.get('active_query')
    selected = st.session_state.get('selected_mode')
    
    for key in list(st.session_state.keys()):
        del st.session_state[key]
        
    if active: 
        st.session_state.active_query = active
    if selected:
        st.session_state.selected_mode = selected
        
    st.session_state.custom_conditions = []
    st.rerun()
