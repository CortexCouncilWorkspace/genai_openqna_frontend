import streamlit as st
import google.cloud.bigquery as bigquery
import os
import sys
import configparser

# Loading Configuration Values
module_path = os.path.abspath(os.path.join('.'))
sys.path.append(module_path)
config = configparser.ConfigParser()
config.read(module_path+'/config.ini')

PROJECT_ID = config['CONFIG']['project_id']
DATASET_ID = config['CONFIG']['dataset_id'] 
REGION_ID = config['CONFIG']['region_id'] 
BACKEND_URL = config['CONFIG']['backend_url']
OPENQNA_DATASET_ID = config['CONFIG']['openqna_dataset_id']
OPENQNA_AUDIT_TABLE = config['CONFIG']['openqna_audit_table']

#Initialize Clients
bqclient = bigquery.Client(project=PROJECT_ID)

#SQL
audit_sql = f"""
    SELECT *
    FROM `{PROJECT_ID}.{OPENQNA_DATASET_ID}.{OPENQNA_AUDIT_TABLE}`;
    """

def call_run_query_bq(audit_sql):
        result_bq = bqclient.query(audit_sql).result().to_dataframe()
        return result_bq

st.set_page_config(layout="wide", page_title="CORA - GenAI - Debug", page_icon="./images/CorAv2Streamlit.png")
with open( "css/style.css" ) as css:
    st.markdown(f'<style>{css.read()}</style>' , unsafe_allow_html= True)
    st.image('./images/Coraheader970x250pxWhite.png')

result_df = call_run_query_bq(audit_sql)
st.dataframe(result_df,use_container_width=False,hide_index=True)
