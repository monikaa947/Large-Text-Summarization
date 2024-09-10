# import streamlit as st
# import vanna as _vn


# @st.cache_data(show_spinner="Generating sample questions ...")
def generate_questions_cached(_vn):
    return _vn.generate_questions()


# @st.cache_data(show_spinner="Generating SQL query ...")
def generate_sql_cached(_vn, question: str):
    return _vn.generate_sql(question=question)


# @st.cache_data(show_spinner="Running SQL query ...")
def run_sql_cached(_vn, sql: str):
    return _vn.run_sql(sql=sql)


# @st.cache_data(show_spinner="Generating Plotly code ...")
def generate_plotly_code_cached(_vn, question, sql, df):
    code = _vn.generate_plotly_code(question=question, sql=sql, df_metadata=df)
    return code


# @st.cache_data(show_spinner="Running Plotly code ...")
def generate_plot_cached(_vn, code, df):
    return _vn.get_plotly_figure(plotly_code=code, df=df)


# @st.cache_data(show_spinner="Generating followup questions ...")
def generate_followup_cached(_vn, question, df):
    return _vn.generate_followup_questions(question=question, df=df)
