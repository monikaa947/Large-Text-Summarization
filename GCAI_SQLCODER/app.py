"""Import all the libraries"""
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import json
import re
import os
import logging
from pathlib import Path
import pandas as pd
import plotly.io as io
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from utils.setup import setup_connexion
from utils.vanna_calls import (generate_plot_cached,
                               generate_plotly_code_cached,
                               generate_sql_cached, run_sql_cached)
from utils.constants import LOG_FORMAT


load_dotenv()
logging.basicConfig(format=LOG_FORMAT,level=logging.DEBUG)
log = logging.getLogger(__name__)
vn = setup_connexion()
app = FastAPI()
origins = [
    "*",  # Allow requests from this origin
    # Add more origins as needed
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class DeleteTrainingData(BaseModel):
    """
    Delete Data structure for the training endpoint
    """
    training_id: str


class PostTrainingData(BaseModel):
    """
    Data structure for the training endpoint
    """
    sql: str
    question: str


class SQLInference(BaseModel):
    """
    Data structure to run inference on the LLM
    """
    question: str


class GetCSVData(BaseModel):
    """
    Data structure for the get CSV data endpoint
    """
    query_dataframe: str


class GetPlotlyChart(BaseModel):
    """
    Data structure for the training endpoint
    """
    # sql: str
    df: str
    question: str


@app.get("/ping")
async def root():
    """
    Heart beat function to test the server status
    """
    return {"message": "pong"}


@app.post("/inference")
async def inference(sql_inference: SQLInference):
    """
    The inference endpoint takes the users natural language query and generates SQL query. 
    
    Returns:
     - Chart (Plotly Figure Object as JSON)
     - Explanation (Summary of the data)
     - Query_Dataframe (Dataframe in stringified JSON)
     - SQL (The SQL Query Generated)
    """

    log.info(sql_inference.question)
    my_question = sql_inference.question
    sql = generate_sql_cached(vn, question=my_question)
    try:
        df = run_sql_cached(vn, sql=sql)
    except Exception as err:
        err_obj = err.with_traceback()
        log.error(err_obj)
        raise HTTPException(status_code=500, detail=f"Error executing the SQL Query\n\n{err_obj}")
    response = {}
    if df is not None:
        code = generate_plotly_code_cached(vn, question=my_question, sql=sql, df=df.dtypes)
        if code is not None and code != "":
            fig = generate_plot_cached(vn, code=code, df=df)
            plot_image = io.to_json(fig=fig,engine='json')
            response['data'] = {"chart": plot_image}

            explanation_prompt = str(re.sub(' +', ' ', f"""[INST]<s>Provide a detailed summary of the \
                                data provided below for the question ask by the user '{my_question}'. \
                                Highlight important points with respect to the question and \
                                provide reasoning of the data. If the data contains only one record \
                                and nothing to compare it against, then generate a summary for a \
                                single record. If the data contains amount or currency then consider \
                                it to be in US Dollars. \
                                \nData:\n\n{df.to_string(index=False)}</s>[/INST]\n\n"""))
            explanation_prompt += f"[INST]{my_question}[/INST]"

            explanation = vn.submit_generate_prompt_secondary(prompt=explanation_prompt)
            
            followup_questions_list = vn.generate_followup_questions(question=my_question,
                                                                     df=df,
                                                                     n_questions=5,
                                                                     sql=sql)
            response['data'].update({"explanation": explanation})
            response['data'].update({"query_dataframe": df.to_json(index=False,orient='split')})
            response['data'].update({'sql': sql})
            response['data'].update({'followup_questions': followup_questions_list})
            
    return response


@app.post("/deleteTrainingData")
async def delete_training_data(delete_training_data :DeleteTrainingData):
    """
    Deletes an entry in the Vector DB.
    """    
    training_id = delete_training_data.training_id
    untrained = vn.remove_training_data(id=training_id)
    return {"untrained": untrained}


@app.post("/postTrainingData")
async def post_training_data(post_training_data : PostTrainingData):
    """
    Creates an entry in the Vector DB to perform RAG by Vanna
    """
    training_question = post_training_data.question
    training_sql = post_training_data.sql
    trained = vn.train(sql=training_sql,question=training_question)
    return {"trained": trained}


@app.get("/getTrainingData")
async def get_training_data():
    """
    Fetches the training data from Vanna
    """
    training_data = vn.get_training_data().to_json(orient="values")
    log.debug(training_data)
    return json.loads(training_data)


@app.get("/question_suggestions")
async def get_common_question():
    """
    Fetches common question the LLM is trained on from vanna.
    """
    question_list = vn.generate_questions()
    return {"data": {"question_suggestions": question_list}}


@app.post("/generatePlot")
async def get_plotly_chart(plotly_data: GetPlotlyChart):
    """
    The generatePlot endpoint returns a new Plotly Chart
    """
    question = plotly_data.question
    df = plotly_data.df
    current_df = pd.DataFrame(pd.read_json(df, orient='split'))
    log.debug(current_df)
    # current_df.dtypes
    response = {}
    code = vn.generate_plotly_code(question=question,df_metadata=current_df.dtypes)
    if code is not None and code != "":
        fig = generate_plot_cached(vn, code=code, df=current_df)
        plot_image = io.to_json(fig=fig,engine='json')
        response['data'] = {"chart": plot_image}
    return response


@app.post("/downloadCSVData")
async def get_csv_data(query_dataframe: GetCSVData):
# async def get_csv_data():

    """
    Download the chart data of the current query as CSV
    """
    log.debug(type(query_dataframe.query_dataframe))
    log.debug(query_dataframe.query_dataframe)
    data_df = pd.DataFrame(pd.read_json(query_dataframe.query_dataframe, orient='split'))
    log.debug(data_df)

    return StreamingResponse(
        content=iter([data_df.to_csv(index=False)]),
        media_type="application/octet-stream",  
        headers={"Content-Disposition": "attachment; filename=data.csv"},
        )


app.mount(
    "/web",
    StaticFiles(directory=Path(__file__).parent.absolute() / "web"),
    name="static",
)


if __name__ == "__main__":
    port = int(os.getenv("port")) or 8004
    uvicorn.run(app=app, port=port)
