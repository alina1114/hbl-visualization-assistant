import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import streamlit as st
import requests
import os
import re
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Load Excel data
df = pd.read_excel(
    r"D:\Desktop\AlinasPrograms\myenv\HBL Proj2\Deposit_Chatbot_Data_Schema.xlsx",
    sheet_name="Deposit_Transactions"
)
df["date"] = pd.to_datetime(df["date"])

# --- Streamlit layout ---
st.set_page_config(page_title="HBL Visualization Assistant", layout="centered")
st.markdown("""
    <style>
        .header-bar {
            background-color: #088F8F;
            padding: 0.7rem 1.2rem;
            border-radius: 0 0 10px 10px;
            margin-top: 1.5rem;
            margin-bottom: 2rem;
        }
        .header-bar h1 {
            font-family: 'Segoe UI', sans-serif;
            color: white;
            text-align: center;
            font-size: 1.8rem;
            margin: 0;
        }
        .stTextInput {
            margin-top: 0.1rem;
        }
        .stTextInput>div>div>input {
            padding: 0.4rem 0.6rem;
            font-size: 0.95rem;
        }
        .block-container {
            padding-top: 3rem !important;
        }
    </style>
    <div class="header-bar">
        <h1>💰 HBL Visualization Assistant</h1>
    </div>
""", unsafe_allow_html=True)

# Query input only
query = st.text_input("Ask a question about the deposit data", placeholder="e.g. Show total deposits by branch in June")

# --- OpenRouter (DeepSeek or Claude) chart generation ---
def ask_openrouter_code(prompt, model = "anthropic/claude-3-haiku"):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "hbl-visualization-assistant"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}\n\nPayload: {payload}\nHeaders: {headers}"

# --- TogetherAI (Meta LLaMA) insight generation ---
def ask_together_insight(prompt, model="meta-llama/Llama-3-8b-chat-hf"):
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful business analyst that summarizes data."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"TogetherAI error: {e}"

# --- Main logic ---
if query:
    st.markdown("### 📊 Chart")

    chart_prompt = f"""
You are a Python assistant. Use matplotlib to create a chart.

You have a pandas DataFrame called df with the following columns:
['transaction_id', 'date', 'branch_id', 'branch_name', 'city', 'region', 'deposit_amount', 'account_type', 'customer_segment']

Instructions:
- Use matplotlib only
- Group and summarize df as needed
- End with plt.show()

User query: "{query}"
"""

    chart_code_response = ask_openrouter_code(chart_prompt)
    match = re.search(r"```(?:python)?\n(.*?)```", chart_code_response, re.DOTALL)
    code = match.group(1).strip() if match else ""

    if code:
        try:
            exec_globals = {"df": df.copy(), "plt": plt, "pd": pd}
            exec(code, exec_globals)
            ax = plt.gca()
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x * 1e-9:.1f}B'))
            for container in ax.containers:
                ax.bar_label(container, fmt='%.0f', padding=3)
            plt.tight_layout()
            st.pyplot(plt)
        except Exception as e:
            st.error(f"⚠️ Error running chart code: {e}")
    else:
        st.info("ℹ️ No chart was generated. Showing insight instead.")

      #  st.markdown("### 🧠 Insight")

    # Always precompute relevant summary based on query
    # Dynamically guess group column based on user query
    # Always precompute relevant summary based on query
    group_column = None
    if "branch" in query.lower():
        group_column = "branch_name"
    elif "account type" in query.lower() or "personal vs business" in query.lower():
        group_column = "account_type"
    elif "customer segment" in query.lower():
        group_column = "customer_segment"
    elif "city" in query.lower():
        group_column = "city"
    elif "region" in query.lower():
        group_column = "region"
    elif "date" in query.lower():
        group_column = "date"

    if group_column:
        summary_df = df.groupby(group_column)["deposit_amount"].sum().reset_index()
        summary_df["deposit_amount"] = summary_df["deposit_amount"].astype("int64")
        summary_df = summary_df.sort_values(by="deposit_amount", ascending=False)
        summary_table = summary_df.to_string(index=False)
    else:
        summary_table = df.head(15).to_string(index=False)

    insight_prompt = f"""
You are a business analyst.

The user asked the following question about deposit data:
"{query}"

The data analyst has provided the result of this query in the form of an aggregated table below:
{summary_table}

Now, write a short business insight (3–5 bullet points) answering the user's question using only the data in this table.

Instructions:
- Focus on answering the query logically based on the table above.
- Mention specific values and percentages if relevant.
- Do NOT reference columns or fields that are not present in the table.
- Do NOT invent any extra facts or context.
- Express values in Pakistani Rupees (PKR), rounded to billions or millions as appropriate.
- Your insight should match the column being summarized.
"""

    insight_response = ask_together_insight(insight_prompt)
    st.success(insight_response.strip())

