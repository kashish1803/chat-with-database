import streamlit as st
import pandas as pd
from db_connect import (
    get_mysql_connection,
    list_mysql_databases,
    get_postgres_connection,
    list_postgres_databases
)
from get_schema import get_database_schema
from llama_client import generate_sql, summarize_results  # ⬅️ updated import
import re

def format_column_name(col_name: str) -> str:
    name = col_name.replace("_", " ")
    name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)
    name = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', name)
    return name.title()

# Streamlit UI setup
st.set_page_config(page_title="Database NLP Chatbot", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
body { background-color: #f8f9fa; font-family: 'Segoe UI', sans-serif; }
.main-title { color: #2c3e50; text-align: center; margin-bottom: 10px; }
.section-header { font-size: 1.2rem; color: #0d6efd; margin-top: 20px; }
div[role='radiogroup'] { margin-top: -25px; margin-bottom: -5px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🛠 LLaMA 3.2 Database NLP Chatbot</h1>", unsafe_allow_html=True)
st.write("Interact with your databases using natural language. Choose your platform, pick a database, and ask any query — the model will generate and summarize the SQL results for you.")

# Step 1: Select platform
st.markdown("<p class='section-header'>1️⃣ Select Database Platform</p>", unsafe_allow_html=True)
db_platform = st.radio("", ["MySQL", "PostgreSQL"], index=0, key="platform_radio")

# Step 2: Select database
if db_platform == "MySQL":
    all_databases = list_mysql_databases()
else:
    all_databases = list_postgres_databases()

if all_databases:
    db_name = st.selectbox(f"Select a {db_platform} database to query:", all_databases, key="db_select")
else:
    st.error(f":material/close: Could not fetch database list. Check {db_platform} connection.")
    db_name = None

# Step 3: Connect and operate
if db_name:
    conn = get_mysql_connection(database=db_name) if db_platform == "MySQL" else get_postgres_connection(database=db_name)
    if conn is None:
        st.error(f":material/close: Could not connect to {db_platform} database.")
    else:
        st.badge(f":material/check: Connected to {db_platform} database: {db_name}", color="green", width="stretch")

        st.markdown("<p class='section-header'>2️⃣ Database Schema</p>", unsafe_allow_html=True)
        schema = get_database_schema(conn, db_name, db_type=db_platform.lower())
        if schema is None:
            st.error(":material/close: Could not fetch database schema.")
        else:
            with st.expander(f":material/code_blocks: View {db_platform} Database Schema"):
                st.json(schema)

            st.markdown("<p class='section-header'>3️⃣ Ask Your Question</p>", unsafe_allow_html=True)
            user_query = st.text_input("Enter your question (e.g., List all employees who have assets under maintenance):")

            if user_query:
                st.badge(":material/autorenew: Generating SQL using LLaMA 3.2...", color="yellow", width="stretch")

                prompt = f"""
You are an expert SQL generator.
Database type: {db_platform}
Database schema (tables, columns, primary keys, foreign keys):
{schema}

Your task:
- Generate the exact SQL query to answer the question.
- Only output SQL - no comments or explanations.
- Always return a syntactically valid SQL query.
- If unsure, still return the best possible SQL.

Generate a valid SQL query to answer:
"{user_query}"
"""

                try:
                    sql_query = generate_sql(prompt).strip()
                    # ------------------ Generated SQL Display ------------------
                    with st.expander(":material/code_blocks: View Generated SQL Query"):
                        st.code(sql_query if sql_query else "-- No SQL generated --", language="sql")

                    # ------------------ NEW FEATURE: SQL Editor ------------------
                    st.markdown("*:blue[:material/drive_file_rename_outline: Modify Generated SQL (Optional)]*")
                    
                    edited_sql = st.text_area(
                        "Edit the SQL if needed:",
                        value=sql_query,
                        height=150
                    )

                    run_modified = st.button("▶ Run Modified SQL")

                    sql_to_execute = edited_sql if run_modified else sql_query
                    is_modified = run_modified  # to identify which was executed

                    # Validate SQL
                    if not sql_to_execute or not sql_to_execute.lower().startswith(("select", "show", "describe")):
                        st.error(":material/close: Invalid SQL query. Modify and try again.")
                    else:
                        with conn.cursor() as cursor:
                            if db_platform == "PostgreSQL":
                                conn.commit()

                            try:
                                cursor.execute(sql_to_execute)
                                results = cursor.fetchall()

                                st.markdown("<p class='section-header'>4️⃣ Query Results</p>", unsafe_allow_html=True)

                                if results:
                                    df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])
                                    df.columns = [format_column_name(col) for col in df.columns]
                                    st.dataframe(df, use_container_width=True, hide_index=True)

                                    # Which SQL executed?
                                    if is_modified:
                                        st.badge(":material/edit: Executed modified SQL query", color="green")
                                    else:
                                        st.badge(":material/bolt: Executed generated SQL query", color="green")

                                    # ------------------ Summary Section ------------------
                                    st.markdown(":material/insights: Summary of Results")
                                    summary = summarize_results(df, user_query)
                                    st.markdown(f"<p style='color:#87CEEB'>{summary}</p>", unsafe_allow_html=True)

                                else:
                                    st.warning(":material/info: Query executed successfully but returned no results.")

                            except Exception as e:
                                st.error(f":material/close: Error executing SQL: {e}")

                except Exception as e:
                    st.error(f":material/close: Error generating or executing SQL: {e}")

        conn.close()
