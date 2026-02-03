import streamlit as st

def apply_custom_style():
    import streamlit as st
    st.markdown("""
        <style>
            /* צבע כפתורים ראשי */
            .stButton>button {
                background-color: #1e429f;
                color: white;
                border-radius: 8px;
                border: none;
                transition: 0.3s;
            }
            .stButton>button:hover {
                background-color: #16367c;
                border: none;
                color: white;
            }
            
            /* עיצוב כותרות */
            h1, h2, h3, h4 {
                color: #1e429f !important;
            }
            
            /* עיצוב Sidebar */
            [data-testid="stSidebar"] {
                background-color: #f0f7ff;
            }
            
            /* עיצוב הודעות מידע (השורות הכחולות שביקשת) */
            .stAlert {
                background-color: #e1effe;
                color: #1e429f;
                border: 1px solid #b2d7ff;
            }

            /* עיצוב ה-Tabs */
            button[data-baseweb="tab"] {
                color: #666;
            }
            button[data-baseweb="tab"][aria-selected="true"] {
                color: #1e429f !important;
                border-bottom-color: #1e429f !important;
            }

            /* שינוי צבע ה-Progress Bar וה-Spinners */
            .stProgress > div > div > div > div {
                background-color: #1e429f;
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
