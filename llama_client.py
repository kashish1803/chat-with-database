import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

API_KEY = os.getenv("HUGGINGFACE_API_KEY")
if not API_KEY:
    raise ValueError("❌ Please set your HUGGINGFACE_API_KEY environment variable.")

client = InferenceClient(api_key=API_KEY)
MODEL_ID = "meta-llama/Llama-3.2-3b-instruct"


def generate_sql(prompt: str) -> str:
    """Generate SQL query from natural language using LLaMA model."""
    try:
        response = client.chat_completion(
            model=MODEL_ID,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert SQL assistant. "
                        "Convert natural language questions into pure SQL queries. "
                        "Output only the SQL query without explanation or markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=256,
            temperature=0.2,
        )

        sql = response.choices[0].message["content"].strip()
        if not sql:
            return "-- No SQL generated --"
        if "```" in sql:
            sql = sql.replace("```sql", "").replace("```", "").strip()

        return sql

    except Exception as e:
        print("❌ Error during SQL generation:", e)
        return f"-- Error generating SQL: {e}"


def summarize_results(df: pd.DataFrame, user_query: str) -> str:
    """
    Summarize the query results using LLaMA model.
    Input: DataFrame and the original user question.
    """
    if df.empty:
        return "No data returned to summarize."

    # Convert small part of the DataFrame to text (limit rows to keep prompt short)
    sample_data = df.head(5).to_markdown(index=False)

    summary_prompt = f"""
You are an analytical assistant.
Here is the user question: "{user_query}"

Here are the first few rows of the query result:
{sample_data}

Write a concise 2-3 sentence natural language summary of the key insights from this data.
Focus only on relevant observations or trends, not SQL.
"""

    try:
        response = client.chat_completion(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": "You are a helpful data summarizer."},
                {"role": "user", "content": summary_prompt},
            ],
            max_tokens=150,
            temperature=0.4,
        )
        summary = response.choices[0].message["content"].strip()
        return summary

    except Exception as e:
        print("❌ Error generating summary:", e)
        return "⚠️ Could not generate summary for the result."
