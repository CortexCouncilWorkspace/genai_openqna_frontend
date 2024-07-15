import google.cloud.bigquery as bigquery
import google.oauth2
import json
import streamlit as st
import random
import os
import sys
import requests
import configparser
from streamlit.components.v1 import html
from streamlit_google_auth import Authenticate
import pandas
import google.auth.transport.requests
import google.oauth2.id_token
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Loading Configuration Values
module_path = os.path.abspath(os.path.join('.'))
sys.path.append(module_path)
config = configparser.ConfigParser()
config.read(module_path+'/config.ini')

PROJECT_ID = config['CONFIG']['project_id']
DATASET_ID = config['CONFIG']['dataset_id'] 
REGION_ID = config['CONFIG']['region_id'] 
BACKEND_URL = config['CONFIG']['backend_url']
AVAILABLE_DATABASES =  config['ENDPOINTS']['available_databases']
GET_KNOWN_SQL =  config['ENDPOINTS']['get_known_sql']
GENERATE_SQL =  config['ENDPOINTS']['generate_sql']
RUN_QUERY =  config['ENDPOINTS']['run_query']
EMBED_SQL = config['ENDPOINTS']['embed_sql']
NATURAL_RESPONSE =  config['ENDPOINTS']['natural_response']
GENERATE_VIZUALIZATION =  config['ENDPOINTS']['generate_vizualization']
user_database = DATASET_ID

assistant_responses = [
        "I'd be glad to help! Here's your answer!",
        "Great question! Let me get your request...",
        "Absolutely!",
        "Of course! Here's the data requested."
        ],
assistant_no_responses = [
       "Hmm, I'm still learning about that. Could you rephrase your question, or provide more context?",
       "I'm not able to find a direct answer right now.",
       "That's a bit outside of my area of expertise.",
       "I'm having trouble to find this information.",
       "It seems like I might need some more training on that topic."
        ]

#Initialize Clients
st.set_page_config(layout="wide", page_title="CORA! - GenAI", page_icon="./images/CorAv2Streamlit.png")
with open( "css/style.css" ) as css:
    st.markdown(f'<style>{css.read()}</style>' , unsafe_allow_html= True)
bqclient = bigquery.Client(project=PROJECT_ID)

# Define Functions

#def make_authorized_get_request(): 
#    auth_req = google.auth.transport.requests.Request()
#    id_token = google.oauth2.id_token.fetch_id_token(auth_req, BACKEND_URL)
#    return id_token

def call_list_databases():
    """Lists available databases in the vector store."""
    endpoint = f"{BACKEND_URL}/available_databases"
    #access_token = make_authorized_get_request()
    #headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(endpoint)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        return data["KnownDB"]  # Return the list of databases
    except requests.exceptions.RequestException as e:
        exception = (f"Error listing databases: {e}")
        return exception

def call_get_known_sql(user_database):
    """Gets suggestive questions for the given database."""
    endpoint = f"{BACKEND_URL}/get_known_sql"
    #access_token = make_authorized_get_request()
    #headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"user_database": user_database}
    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["KnownSQL"]
    except requests.exceptions.RequestException as e:
        print(f"Error getting known SQL: {e}")
        return None

def call_generate_sql(user_question, user_database):
    """Generates SQL for a given question and database."""
    endpoint = f"{BACKEND_URL}/generate_sql"
    #access_token = make_authorized_get_request()
    #headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"user_question": user_question, "user_database": user_database}
    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        data = response.json()
        #return data["GeneratedSQL"]
        return data
    except requests.exceptions.RequestException as e:
        exception = (f"Error generating SQL: {e}")
        return exception


def call_run_query(user_database, generated_sql):
    """Executes the SQL statement against the database."""
    endpoint = f"{BACKEND_URL}/run_query"
    #access_token = make_authorized_get_request()
    #headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"user_database": user_database, "generated_sql": generated_sql}
    try:
        response = requests.post(endpoint, json=payload)
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
    endpoint = f"{BACKEND_URL}/embed_sql"
    #access_token = make_authorized_get_request()
    #headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "user_question": user_question,
        "generated_sql": generated_sql,
        "user_database": user_database,
    }
    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error embedding SQL: {e}")
        return False

def call_natural_response(user_question, user, sql_results):
    """Generates SQL for a given question and database."""
    endpoint = f"{BACKEND_URL}/natural_response"
    #access_token = make_authorized_get_request()
    #headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"user_question": user_question, "user_database": user_database}
    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["NaturalResponse"]
    except requests.exceptions.RequestException as e:
        print(f"Error generating SQL: {e}")
        return None
    
def call_generate_viz(user_question, sql_generated, sql_results):
    """Generates Google Charts code based on SQL results."""
    endpoint = f"{BACKEND_URL}/generate_viz"
    #access_token = make_authorized_get_request()
    #headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "user_question": user_question,
        "sql_generated": sql_generated,
        "sql_results": sql_results
    }
    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()["GeneratedChartjs"]
    except requests.exceptions.RequestException as e:
        print(f"Error generating visualization: {e}")
        return None


#Build Frontend

st.image('./images/Coraheader970x250pxWhite_Portuguese.png', use_column_width="auto")
with st.expander("**Clique para ver instruções e exemplos de perguntas!**", expanded=False):
    st.text(f"""
                Trabalho em progresso!
                """)
col1, col2, col3 = st.columns([5,3,5])
with col2:
    generate_graph = st.toggle('Experimental: Mostrar Gráficos?', value=False, key=None, help=None, on_change=None, args=None, kwargs=None, disabled=False, label_visibility="visible")
if "session_data" not in st.session_state:
    st.session_state.session_data = {
        "messages": [],
    }
for message in st.session_state.session_data["messages"]:
    with st.chat_message(message["role"], avatar=('./images/Userv2_128px.png' if message["role"] == 'human' else './images/CorAv2Streamlit.png')):
        if message["role"] == 'human':
            st.markdown(message["content"])
        else:
            if message["ok_code"] == 200:
                st.markdown(message["content"])
                with st.expander("Dados Solicitados:", expanded=True):
                    if generate_graph:
                        tab1, tab2, tab3, tab4 = st.tabs(["Gráfico 1", "Gráfico 2", "Dados", "SQL"])
                        with tab1:
                            html(f"""
                            <html>
                                <head>
                                    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
                                    <script type="text/javascript">
                                        {message["Graph1"]}
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
                                        {message["Graph2"]}
                                    </script>
                                </head>
                                <body>
                                    <div id="chart_div_1"></div>
                                </body>
                            </html>
                            """,width=800,height=500,scrolling=False)
                        tab3.dataframe(message["Dados"],use_container_width=True,hide_index=True)
                        tab4.write(message["SQL"])
                    else:
                        tab3, tab4 = st.tabs(["Dados", "SQL"])
                        tab3.dataframe(message["Dados"],use_container_width=True,hide_index=True)
                        tab4.write(message["SQL"])
            elif message["ok_code"] == 201:
                st.markdown(message["content"])
                with st.expander("SQL Gerado:", expanded=True):
                    st.write(message["SQL"])
            else:
                st.markdown(message["content"])

if prompt := st.chat_input("Deixe-me mostrar minha mágica, me faça uma pergunta!"):
    st.chat_message("human", avatar='./images/Userv2_128px.png').markdown(prompt)
    st.session_state.session_data["messages"].append({"role": "human", "content": prompt})
    
    with st.chat_message("assistant", avatar='./images/CorAv2Streamlit.png'):
        with st.spinner("Fazendo a mágica!!!"):
            result_sql_code = call_generate_sql(prompt, user_database)
            if result_sql_code["ResponseCode"] == 200:
                result_df = call_run_query_bq(result_sql_code["GeneratedSQL"])
                if not result_df.empty:              
                    result_json = pandas.DataFrame.to_json(result_df.head(12),orient="records")
                    result_graph = call_generate_viz(prompt,result_sql_code["GeneratedSQL"],result_json)
                    ai_response = "Ficarei feliz em ajudar! Aqui está sua resposta!"
                    st.session_state.session_data["messages"].append({"role": "assistant", "content": ai_response, "ok_code": 200, "Dados": result_df, "SQL": result_sql_code["GeneratedSQL"], "Graph1": result_graph["chart_div"], "Graph2": result_graph["chart_div_1"]})
                    st.rerun() 
                else:
                    ai_response = "A consulta foi gerada com sucesso, mas não retornou nenhum dado, solicite dados diferentes!"
                    with st.expander("Visualize a consulta gerada!"):
                        st.write(result_sql_code["GeneratedSQL"])
                    st.session_state.session_data["messages"].append({"role": "assistant", "content": ai_response, "ok_code": 201, "Dados": [], "SQL": result_sql_code["GeneratedSQL"], "Graph1": [], "Graph2": []})    
                    st.rerun() 
            else:
                ai_response = "Hmm, ainda estou aprendendo sobre isso. Você poderia reformular sua pergunta ou fornecer mais contexto?"
                st.session_state.session_data["messages"].append({"role": "assistant", "content": ai_response, "ok_code": 500, "Dados": [], "SQL": [], "Graph1": [], "Graph2": []})
                st.rerun()