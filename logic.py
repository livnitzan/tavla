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
            transition: 0.2s;
        }
        
        .stButton>button:hover {
            background-color: #E2E6EA !important;
            border-color: #ADB5BD !important;
            color: #212529 !important;
        }
        
        /* הודעות מערכת בכחול עדין */
        div[data-testid="stNotification"] { 
            background-color: #E3F2FD !important; 
            color: #0D47A1 !important; 
            border: 1px solid #BBDEFB !important;
        }

        /* תיקון לכפתור Primary (כמו 'הרץ ניתוח') שיישאר בולט אך תואם */
        button[data-testid="baseButton-primary"] {
            background-color: #0D47A1 !important;
            color: white !important;
            border: none !important;
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
