import re
import json
import logging
import requests
import pandas as pd
from vanna.base import VannaBase
from vanna.types import TrainingPlan, TrainingPlanItem
from utils.utils import chat_prompt_generator_duex, prompt_generator, prompt_generator_duex
from utils.constants import LOG_FORMAT


logging.basicConfig(format=LOG_FORMAT,level=logging.DEBUG)
log = logging.getLogger(__name__)


class Ollama(VannaBase):
    """
    A custom Ollama interface to interact with models hosted by Ollama server.
    """
    def __init__(self, config=None):
        if config is None or "ollama_host" not in config:
            self.host = "http://localhost:11434"
        else:
            self.host = config["ollama_host"]

        if config is None or "model" not in config:
            raise ValueError("config must contain a Ollama model for SQL generation")
        else:
            self.model = config["model"]
   
        if config is None or "secondary_model" not in config:
            raise ValueError("config must contain a Ollama model for Plot & Summary generation")
        else:
            self.secondary_model = config["secondary_model"]


    def system_message(self, message: str) -> any:
        return {"role": "system", "content": message}


    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}


    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}


    def extract_sql_query(self, text):
        """
        Extracts the first SQL statement after the word 'select', ignoring case,
        matches until the first semicolon, three backticks, or the end of the string,
        and removes three backticks if they exist in the extracted string.

        Args:
        - text (str): The string to search within for an SQL statement.

        Returns:
        - str: The first SQL statement found, with three backticks removed,\
        or an empty string if no match is found.
        """
        # Regular expression to find 'select' (ignoring case) and capture until ';', '```', or end of string
        pattern = re.compile(r"select.*?(?:;|```|$)", re.IGNORECASE | re.DOTALL)

        match = pattern.search(text)
        if match:
            # Remove three backticks from the matched string if they exist
            return match.group(0).replace("```", "")
        else:
            return text


    def generate_sql(self, question: str, allow_llm_to_see_data=False, **kwargs) -> str:
        """
        Args:
            question (str): The question to generate a SQL query for.

        Returns:
            str: The SQL query that answers the question.
        """
        question_sql_list =  self.get_similar_question_sql(question, **kwargs)
        doc_list = self.get_related_documentation(question, **kwargs)

        # prompt = prompt_generator(question_sql_list, doc_list, question)
        prompt = prompt_generator_duex(question_sql_list=question_sql_list,
                                            doc_list=doc_list,
                                            question=question)
        log.info(prompt)
        llm_response = self.submit_generate_prompt(prompt, **kwargs)
        log.debug(llm_response)
        # Use the super generate_sql
        sql = self.extract_sql(llm_response)
        # Replace "\_" with "_"
        sql = sql.replace("\\_", "_")
        sql = sql.replace("\\", "")

        return self.extract_sql_query(sql)


    def generate_plotly_code(
        self, question: str = None, sql: str = None, df_metadata: str = None, **kwargs
    ) -> str:
        if question is not None:
            system_msg = f"[INST]<s>The following is a pandas DataFrame that contains the results \
            of the query that answers the question the user asked: '{question}'"
        else:
            system_msg = "[INST]<s>The following is a pandas DataFrame "

        if sql is not None:
            system_msg += f"\n\nThe DataFrame was produced using this query: {sql}\n\n"

        system_msg += f"The following is information about the resulting pandas DataFrame \
            'df': \n{df_metadata}</s>[/INST]\n\n"

        system_msg += "[INST]Can you generate the Python plotly code to chart the results of the \
                dataframe? Assume the data is in a pandas dataframe called 'df'. If there is only one value \
                in the dataframe, use an Indicator. Respond with only Python code. Do not answer \
                with any explanations -- just the code.[/INST]"

        plotly_code = self.submit_generate_prompt_secondary(system_msg, kwargs=kwargs)

        return self._sanitize_plotly_code(self._extract_python_code(plotly_code))


    def submit_prompt(self, prompt, **kwargs) -> str:
        url = f"{self.host}/api/chat"
        data = {    
            "model": self.model,
            "stream": False,
            "messages": prompt,
            "options": {
                "num_ctx": 16394,
                "seed": 72
            }
        }

        response = requests.post(url, json=data)

        log.debug(response)
        response_dict = response.json()
        return response_dict["message"]["content"]


    def submit_generate_prompt(self, prompt, **kwargs) -> str:
        """
        Call Ollama /api/generate endpoint to generate SQL Query
        """
        url = f"{self.host}/api/generate"
        data = json.dumps({
            "model": self.model,
            "stream": False,
            "prompt": prompt,
            "keep_alive": "300s",
            "options": {
                "seed": 72,
                "num_predict": 150
            }
        })

        response = requests.post(url, data=data)
        response_dict = response.json()
        log.debug(response_dict)
        return response_dict["response"]


    def submit_generate_prompt_secondary(self, prompt, **kwargs) -> str:
        """
        Call Ollama /api/generate endpoint to generate SQL Query
        """
        url = f"{self.host}/api/generate"
        if self.secondary_model:
            model = self.secondary_model
        else:
            model = self.model
        data = json.dumps({
            "model": model,
            "stream": False,
            "prompt": prompt,
            "keep_alive": "300s",
            "options": {
                "seed": 72
            }
        })

        response = requests.post(url, data=data)
        response_dict = response.json()
        log.debug(response_dict)
        return response_dict["response"]

    def generate_questions(self, **kwargs) -> list[str]:
        """
        **Example:**
        ```python
        vn.generate_questions()
        ```

        Generate a list of questions that you can ask Vanna.AI.
        """
        question_sql = self.get_similar_question_sql(question="", **kwargs)
        return [q["question"] for q in question_sql]


    def get_training_plan_generic(self, df, **kwargs) -> TrainingPlan:
        """
        This method is used to generate a training plan from an information schema dataframe.

        Basically what it does is breaks up INFORMATION_SCHEMA.COLUMNS into groups of table/column\
            descriptions that can be used to pass to the LLM.

        Args:
            df (pd.DataFrame): The dataframe to generate the training plan from.

        Returns:
            TrainingPlan: The training plan.
        """
        table_column = df.columns[
            df.columns.str.lower().str.contains("table_name")
        ].to_list()[0]
        columns = [
            # database_column,
            #         schema_column,
                    table_column]
        candidates = ["column_name",
                      "data_type",
                      "comment"]
        matches = df.columns.str.lower().str.contains("|".join(candidates), regex=True)
        columns += df.columns[matches].to_list()

        plan = TrainingPlan([])

        for table in (
            df[table_column]
            .unique()
            .tolist()
        ):
            df_columns_filtered_to_table = df.query(
                f'{table_column} == "{table}"'
            )
            doc = f"""The following columns are in the {table} table.\n\n """
            doc += f"""CREATE TABLE {table} ({','.join([' '.join(column_data)
            for column_data in df_columns_filtered_to_table[columns[1:]].values])})"""

            plan._plan.append(
                TrainingPlanItem(
                    item_type=TrainingPlanItem.ITEM_TYPE_IS,
                    item_group="",
                    item_name=table,
                    item_value=doc,
                )
            )
        return plan


    def generate_followup_questions(self, question: str, sql: str, df: pd.DataFrame, n_questions: int = 5, **kwargs) -> list:
        """
        **Example:**
        ```python
        vn.generate_followup_questions("What are the top 10 customers by sales?", sql, df)
        ```

        Generate a list of followup questions that you can ask Vanna.AI.

        Args:
            question (str): The question that was asked.
            sql (str): The LLM-generated SQL query.
            df (pd.DataFrame): The results of the SQL query.
            n_questions (int): Number of follow-up questions to generate.

        Returns:
            list: A list of followup questions that you can ask Vanna.AI.
        """
        doc_list = self.get_related_documentation(question, **kwargs)
        doc_list = '\n\n'.join(doc_list)
        message_log = f"[INST]<s>You are a helpful data assistant. The user asked the question: \
        '{question}'\n\nThe SQL query for this question was: {sql}\n\n \
        The following is a pandas DataFrame with the results of the query: \
        \n{df.to_string(index=False)}.The SQL query was generated with strict reference to these table schema: {doc_list} \n\n</s>[/INST]"

        message_log +=f"[INST]Generate a list of {n_questions} followup questions that the user might \
        ask about this data. Respond with a list of questions, one per line. Do not answer with \
        any explanations -- just the questions like 'Question:'. Remember that there should be an unambiguous SQL \
        query that can be generated from the question. Prefer questions that are answerable outside \
        of the context of this conversation. Prefer questions that are slight modifications of the \
        SQL query that was generated that allow digging deeper into the data. Each question will \
        be turned into a button that the user can click to generate a new SQL query so don't use \
        'example' type questions. Each question must have a one-to-one correspondence with an \
        instantiated SQL query like 'SQL:'.[/INST]\n\n"
        
        
        

        llm_response = self.submit_generate_prompt_secondary(message_log, **kwargs)

        numbers_removed = re.sub(r"^\d+\.\s*", "", llm_response.strip(), flags=re.MULTILINE)
        log.debug(numbers_removed)
        return [ {'followup_question': fupq.split("\n")[0].split("Question:")[1].strip().strip("\""), 
                    'sql': fupq.split("SQL:")[1]}  
                for fupq in numbers_removed.split("\n\n")]

