import streamlit as st

def apply_custom_style():
    """החלת עיצוב עם הכחול המדויק מהתמונה (RTL ונייטרליות)"""
    st.markdown("""
        <style>
        /* RTL בסיסי */
        .main { direction: RTL; text-align: right; }
        [data-testid="stSidebar"] { direction: RTL; text-align: right; }
        div.stApp { direction: RTL; }

        /* צבע הכחול מהתמונה לתוויות נבחרות (כמו 'ליגת העל') */
        span[data-baseweb="tag"] {
            background-color: #4482eb !important;
        }

        /* צבע לטקסט של תוויות (Labels) */
        .stSelectbox label, .stMultiSelect label, .stRadio label {
            color: #31333F !important;
            font-weight: 500;
        }

        /* כפתורים אפורים נייטרליים (כמו במחשב שלך) */
        .stButton>button { 
            width: 100%; border-radius: 5px; 
            background-color: #F8F9FA !important; color: #495057 !important;
            border: 1px solid #CED4DA !important;
            font-size: 14px;
        }
        
        .stButton>button:hover {
            background-color: #E2E6EA !important;
            border-color: #ADB5BD !important;
            color: #212529 !important;
        }

        /* הודעות מערכת בכחול בהיר תואם */
        div[data-testid="stNotification"] { 
            background-color: #E8F0FE !important; 
            color: #1967D2 !important; 
            border: 1px solid #D2E3FC !important;
        }

        /* צבע כחול לסליידר ולכפתורי רדיו */
        .stSlider [data-baseweb="slider"] > div > div {
            background-color: #4482eb !important;
        }
        </style>
        """, unsafe_allow_html=True)
