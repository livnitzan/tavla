import streamlit as st

def apply_custom_style():
    """החלת עיצוב CSS מנקודת המוצא (RTL, כפתורים אפורים, הודעות כחולות)"""
    st.markdown("""
        <style>
        .main { direction: RTL; text-align: right; }
        [data-testid="stSidebar"] { direction: RTL; text-align: right; }
        [data-testid="stDataFrame"] { direction: RTL; width: 100%; }
        div[data-testid="stDataFrame"] > div { width: 100% !important; }
        
        /* כפתורים אפורים נייטרליים */
        .stButton>button { 
            width: 100%; border-radius: 5px; 
            background-color: #F8F9FA !important; color: #495057 !important;
            border: 1px solid #CED4DA !important;
        }
        
        /* הודעות מערכת בכחול */
        div[data-testid="stNotification"] { 
            background-color: #E3F2FD !important; 
            color: #0D47A1 !important; 
            border: 1px solid #BBDEFB !important;
        }
        </style>
        """, unsafe_allow_html=True)

def reset_params():
    """איפוס פרמטרים וחזרה למצב נקי"""
    active = st.session_state.get('active_query')
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    if active: 
        st.session_state.active_query = active
    st.session_state.custom_conditions = []
    st.rerun()