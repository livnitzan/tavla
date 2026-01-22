import streamlit as st
import pandas as pd

def apply_custom_style():
    """מחיל עיצוב RTL ו-CSS כללי למערכת"""
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { direction: rtl; }
            [data-testid="stHorizontalBlock"] { direction: rtl; }
            .stMarkdown { direction: rtl; text-align: right; }
            .stDataFrame { direction: rtl; }
        </style>
    """, unsafe_allow_html=True)

get_season_data(client=None, season=2024):
    # אם לא נשלח client, נחזיר דיקשנרי ריק או ברירת מחדל כדי לא לקרוס
    if client is None:
        return {2024: 36, 2023: 36, 2022: 36}
    """
    פונקציה מרכזית לשליפת נתוני עונה. 
    המודולים שלך (הטבלה ומלכי השערים) קוראים לה כדי לקבל את הבסיס.
    """
    where_clause = f"WHERE season = {season}"
    if league:
        where_clause += f" AND league = '{league}'"
    
    # שאילתה גנרית שמתאימה למבנה הטבלאות שלך
    query = f"SELECT * FROM `tavla-440015.table.games` {where_clause}"
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.error(f"שגיאה בשליפת נתוני עונה: {e}")
        return pd.DataFrame()

def get_filter_options(df):
    """מחלץ אפשרויות לסינון (קבוצות, מפעלים וכו') מתוך ה-DataFrame"""
    if df is None or df.empty:
        return []
    return sorted(df['team'].unique().tolist()) if 'team' in df.columns else []

def reset_params():
    """מנקה את המטמון של האפליקציה"""
    st.cache_data.clear()
    if 'last_query_result' in st.session_state:
        del st.session_state.last_query_result
