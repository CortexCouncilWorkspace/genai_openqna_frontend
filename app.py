import google.cloud.bigquery as bigquery
from google.oauth2 import service_account
import json
import streamlit as st
import random
import os
import sys
import requests
import configparser
from streamlit.components.v1 import html
import pandas

# Loading Configuration Values
module_path = os.path.abspath(os.path.join('.'))
sys.path.append(module_path)
config = configparser.ConfigParser()
config.read(module_path+'/config.ini')

PROJECT_ID = config['CONFIG']['project_id']
DATASET_ID = config['CONFIG']['dataset_id'] 
REGION_ID = config['CONFIG']['region_id'] 
BACKEND_URL = config['CONFIG']['backend_url']
user_database = DATASET_ID
assistant_responses =  [
        "I'd be glad to help! Here's your answer!",
        "Great question! Let me get your request...",
        "Absolutely!",
        "Of course! Here's the data requested."
        ]
assistant_no_responses=[
       "Hmm, I'm still learning about that. Could you rephrase your question, or provide more context?",
       "I'm not able to find a direct answer right now.",
       "That's a bit outside of my area of expertise.",
       "I'm having trouble to find this information.",
       "It seems like I might need some more training on that topic."
        ]

#Initialize Clients
bqclient = bigquery.Client(project=PROJECT_ID)

# Define API Functions

def call_list_databases():
    """Lists available databases in the vector store."""
    url = f"{BACKEND_URL}/available_databases"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        return data["KnownDB"]  # Return the list of databases
    except requests.exceptions.RequestException as e:
        exception = (f"Error listing databases: {e}")
        return exception


def call_get_known_sql(user_database):
    """Gets suggestive questions for the given database."""
    url = f"{BACKEND_URL}/get_known_sql"
    payload = {"user_database": user_database}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["KnownSQL"]
    except requests.exceptions.RequestException as e:
        print(f"Error getting known SQL: {e}")
        return None

def call_generate_sql(user_question, user_database):
    """Generates SQL for a given question and database."""
    url = f"{BACKEND_URL}/generate_sql"
    payload = {"user_question": user_question, "user_database": user_database}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["GeneratedSQL"]
    except requests.exceptions.RequestException as e:
        exception = (f"Error generating SQL: {e}")
        return exception


def call_run_query(user_database, generated_sql):
    """Executes the SQL statement against the database."""
    url = f"{BACKEND_URL}/run_query"
    payload = {"user_database": user_database, "generated_sql": generated_sql}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["KnownDB"]  # Return query results
    except requests.exceptions.RequestException as e:
        print(f"Error running query: {e}")
        return None
    
def call_run_query_bq(generated_sql):
        result_bq = bqclient.query(generated_sql).result().to_dataframe()
        return result_bq


def call_embed_sql(user_question, generated_sql, user_database):
    """Embeds known good SQLs."""
    url = f"{BACKEND_URL}/embed_sql"
    payload = {
        "user_question": user_question,
        "generated_sql": generated_sql,
        "user_database": user_database,
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error embedding SQL: {e}")
        return False

def call_natural_response(user_question, user, sql_results):
    """Generates SQL for a given question and database."""
    url = f"{BACKEND_URL}/natural_response"
    payload = {"user_question": user_question, "user_database": user_database}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["NaturalResponse"]
    except requests.exceptions.RequestException as e:
        print(f"Error generating SQL: {e}")
        return None
    
def call_generate_viz(user_question, sql_generated, sql_results):
    """Generates Google Charts code based on SQL results."""
    url = f"{BACKEND_URL}/generate_viz"
    payload = {
        "user_question": user_question,
        "sql_generated": sql_generated,
        "sql_results": sql_results
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["GeneratedChartjs"]
    except requests.exceptions.RequestException as e:
        print(f"Error generating visualization: {e}")
        return None





#Build Frontend
st.set_page_config(layout="wide", page_title="GenAI - COPEL", page_icon="./images/CorAv2Streamlit.png")
with open( "css/style.css" ) as css:
    st.markdown(f'<style>{css.read()}</style>' , unsafe_allow_html= True)
    st.image('./images/Copel_header.png')

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=('./images/UserCopel.png' if message["role"] == 'human' else './images/CopelAss.png')):
        st.markdown(message["content"])

if prompt := st.chat_input("O que você está buscando?"):
    st.chat_message("human", avatar='./images/UserCopel.png').markdown(prompt)
    st.session_state.messages.append({"role": "human", "content": prompt})
    
    with st.chat_message("assistant", avatar='./images/CopelAss.png'):
         with st.spinner("Trabalhando..."):
            result_sql_code = call_generate_sql(prompt, user_database)
            if result_sql_code:
                result_df = call_run_query_bq(result_sql_code)
                result_json = pandas.DataFrame.to_json(result_df,orient="records")
                result_graph = call_generate_viz(prompt,result_sql_code, result_json)
                ai_response = random.choice(assistant_responses)
                st.write(ai_response)
                tab1, tab2, tab3, tab4 = st.tabs(["Gráfico 1","Gráfico 2", "Dados", "SQL"])
                with tab1:
                    html(f"""
                    <html>
                        <head>
                            <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
                            <script type="text/javascript">
                                {result_graph["chart_div"]}
                            </script>
                        </head>
                        <body>
                            <div id="chart_div"></div>
                        </body>
                    </html>
                    """,width=800,height=500,scrolling=False)
                with tab2:
                    html(f"""
                    <html>
                        <head>
                            <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
                            <script type="text/javascript">
                                {result_graph["chart_div_1"]}
                            </script>
                        </head>
                        <body>
                            <div id="chart_div_1"></div>
                        </body>
                    </html>
                    """,width=800,height=500,scrolling=False)
                tab3.dataframe(result_df,use_container_width=True,hide_index=True) 
                tab4.write(result_sql_code)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            else:
                ai_response = random.choice(assistant_no_responses)
                st.write(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})

