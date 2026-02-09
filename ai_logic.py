import streamlit as st
import pandas as pd
import requests
import json
import time

# הגדרות מפתח ומודל
api_key = "AIzaSyCgAzsLlYW60R_5OL-6hxTkyMxlqDa8LO0"
model_name = "models/gemini-3-flash-preview"

def translate_user_query_to_sql(user_text, limit_val):
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    limit_clause = f"limit {limit_val}" if limit_val else ""
    
    prompt_context = f"""
    you are a bigquery sql expert. return only the sql code in lowercase.
    
    tables:
    1. `tavla-440015.table.srtdgms` as s: match data (game_id, season, team, rival, gf, ga, date, forfeit, comp_id).
    2. `tavla-440015.table.degoals` as d: goals data (game_id, scorrer, team, winner, minute, gorder).
    3. `tavla-440015.table.teams` as t: mapping table (team_id, team).
    4. `tavla-440015.table.comps` as c: competition names (comp_id, comp).

    critical rules:
    - sorting: always order by s.date asc, s.game_id asc, d.gorder asc.
    - join condition: always use `on s.game_id = d.game_id and s.team = d.team`.
    - search logic: use 'like %name%' ONLY for text names. use '=' for numbers/seasons.
    - forfeit filter: always use `where (s.forfeit is false or s.forfeit is null)`.
    - ambiguity: always prefix columns with table aliases (s.date, d.scorrer, etc.).
    - scorrer column: if the query specifies exactly one player name, omit 'd.scorrer'. otherwise, include it.
    - display: select s.date, c.comp, s.season, t1.team as team_name, t2.team as rival_name, d.scorrer, d.minute.
    - do not include game_id or gorder in the final select.
    - no aggregations. return raw rows.
    {limit_clause}
    """

    payload = {"contents": [{"parts": [{"text": f"{prompt_context}\n\nquestion: {user_text}\n\nsql:"}]}]}
    try:
        response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        sql = response.json()['candidates'][0]['content']['parts'][0]['text']
        return sql.replace("```sql", "").replace("```", "").strip()
    except:
        return "error"

def generate_natural_language_answer(user_question, data_df):
    """
    מייצרת תשובה מילולית שרק סופרת את המקרים ללא פירוט.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    count_rows = len(data_df)
    data_summary = data_df.to_string(index=False)
    
    # הנחיה לסיכום מספרי בלבד
    prompt = f"""
    על בסיס הנתונים הבאים, ענה על השאלה: "{user_question}"
    חוקים לתשובה:
    1. ציין רק את הכמות הכוללת של המקרים שנמצאו (יש {count_rows} שורות בנתונים).
    2. אל תפרט שמות שחקנים, תאריכים או קבוצות בתשובה הזו.
    3. כתוב משפט קצר אחד בעברית, למשל: "נמצאו X מקרים המתאימים לבקשתך."
    
    הנתונים:
    {data_summary}
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except:
        return f"נמצאו {count_rows} תוצאות המתאימות לשאלתך:"

def show_ai_query_interface(db_client):
    st.title("🔍 ניתוח נתונים חופשי (Gemini 3)")

    limit_options = ["ללא הגבלה", 5, 10, 20, 50, 100]
    
    with st.form("ai_search_form"):
        selected_limit = st.selectbox("מספר תוצאות להצגה:", limit_options, index=0)
        sql_limit = None if selected_limit == "ללא הגבלה" else selected_limit
        user_input = st.text_input("מה תרצה לדעת?", placeholder="למשל: כל השערים של מכבי תל אביב נגד מכבי חיפה")
        submit_button = st.form_submit_button("חפש נתונים")

    if submit_button and user_input:
        start_time = time.time()
        
        with st.spinner("Gemini 3 מסכם את הנתונים..."):
            sql_query = translate_user_query_to_sql(user_input, sql_limit)
            
            if "error" not in sql_query:
                try:
                    results_df = db_client.query(sql_query).to_dataframe()
                    elapsed_time = round(time.time() - start_time, 2)
                    
                    if not results_df.empty:
                        # הצגת הסיכום המספרי בלבד
                        st.info(generate_natural_language_answer(user_input, results_df))
                        
                        # הצגת הטבלה המפורטת
                        st.subheader(f"📋 פירוט מלא")
                        st.dataframe(results_df, use_container_width=True)
                        
                        st.caption(f"⏱️ זמן ביצוע: {elapsed_time} שניות")
                        with st.expander("ראה את קוד ה-SQL שנוצר"):
                            st.code(sql_query, language="sql")
                    else:
                        st.warning("לא נמצאו נתונים.")
                        st.caption(f"⏱️ זמן ביצוע: {elapsed_time} שניות")
                except Exception as e:
                    st.error("השאילתה נכשלה בהרצה.")
                    st.code(sql_query)
                    st.caption(f"פרטים: {e}")