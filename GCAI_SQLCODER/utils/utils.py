#Import libraries
from  functools import reduce
from utils.constants import *

def get_sql_ques_instruction_generator(merge, sql_ques) -> str:
    """
    This method transforms the dict type data structure to instruction fine-tuned prompts.

    arguments: 
        merge: initialise to an empty string
        sql_ques: pass the next dict item containing SQL and Question
    
    return:
        prompt:  instruction fine-tuned prompt  
    """
    merge += f"""[INST]{sql_ques['question']}[/INST]\nSQL_Query: ```{sql_ques['sql']}```\n"""
    return  merge


def prompt_generator(question_sql_list, doc_list, question) -> str:
    """
    Generate prompt to fetch SQL Query using RAG.
    arguments:
        question_sql_list: A Dict type List to fetch question and sql from the vector database.
        doc_list: A List of database schema.
        question: Query asked by the end user.
    
    return:
        prompt: A string prompt to generate a sql query.
    """
    initial_prompt = SQL_RAG_INITIAL_PROMPT
    final_prompt  = f"{initial_prompt}\n\n"
    if isinstance(doc_list, list) and (len(doc_list) != 0):
        doc_list_merged = '\n\n'.join(doc_list)
        final_prompt += f"""[INST] DOCUMENTATION:
        ------------------------------------------- DOCUMENTATION BEGINS --------------------------------
        {doc_list_merged}
        ------------------------------------------- DOCUMENTATION ENDS --------------------------------
        [/INST]"""
    if isinstance(question_sql_list, list) and (len(question_sql_list) != 0):
        final_prompt += reduce(get_sql_ques_instruction_generator,question_sql_list,"")
    final_prompt += f"""</s>\n [INST] User: {question} [/INST]"""
    return final_prompt

def get_sql_ques_instruction_generator_duex(merge, sql_ques) -> str:
    """
    This method transforms the dict type data structure into fine-tuned prompts.

    arguments: 
        merge: initialise to an empty string
        sql_ques: pass the next dict item containing SQL and Question
    
    return:
        prompt:  instruction fine-tuned prompt  
    """
    merge += f"""-- {sql_ques['question']}: ```{sql_ques['sql']}```\n"""
    return  merge


def prompt_generator_duex(question_sql_list, doc_list, question) -> str:
    """
    Generate prompt to fetch SQL Query using RAG.
    arguments:
        question_sql_list: A Dict type List to fetch question and sql from the vector database.
        doc_list: A List of database schema.
        question: Query asked by the end user.
    
    return:
        prompt: A string prompt to generate a sql query.
    """
    prompt = ""
    initial_prompt = SQL_RAG_INITIAL_PROMPT_DUEX
    final_prompt =  SQL_RAG_FINAL_PROMPT_DUEX.format(question=question)

    #Adding system message to the prompt
    prompt += initial_prompt
    if isinstance(doc_list, list) and (len(doc_list) != 0):
        doc_list_merged = '\n\n'.join(doc_list)
        prompt += doc_list_merged

    if isinstance(question_sql_list, list) and (len(question_sql_list) != 0):
        prompt += reduce(get_sql_ques_instruction_generator_duex,
                         question_sql_list,
                         "Examples\n")

    prompt += final_prompt
    return prompt


def chat_prompt_generator_duex(question_sql_list, doc_list, question, vanna) -> list:
    """
    Generate prompt to fetch SQL Query using RAG.
    arguments:
        question_sql_list: A Dict type List to fetch question and sql from the vector database.
        doc_list: A List of database schema.
        question: Query asked by the end user.
        vanna: vanna intiantiated object.
    
    return:
        prompt: A string prompt to generate a sql query.
    """
    prompt = []
    system_prompt = ""
    initial_prompt = SQL_RAG_INITIAL_PROMPT_DUEX
    final_prompt =  SQL_RAG_FINAL_PROMPT_DUEX.format(question=question)

    #Adding system message to the prompt
    system_prompt += initial_prompt
    if isinstance(doc_list, list) and (len(doc_list) != 0):
        doc_list_merged = '\n\n'.join(doc_list)
        system_prompt += doc_list_merged

    if isinstance(question_sql_list, list) and (len(question_sql_list) != 0):
        system_prompt += reduce(
            get_sql_ques_instruction_generator_duex,
            question_sql_list,
            "Examples\n")

    prompt.append(vanna.system_message(system_prompt))
    prompt.append(vanna.user_message(final_prompt))

    return prompt
