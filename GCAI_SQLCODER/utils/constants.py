SQL_RAG_INITIAL_PROMPT = """<s>[INST] User: The user provides a question and you provide Oracle Database SQL. You will only respond with Oracle Database SQL code and not with any explanations. Respond with only Oracle Database SQL code. Do not answer with any explanations -- just the code. You may use the following documentation as a reference for what tables might be available. Use responses of past questions to guide you:[/INST]"""
SQL_RAG_INITIAL_PROMPT_DUEX = """### Instructions: Convert the user's question into an Oracle Database SQL query. Follow these rules strictly!\n\n

- **Respond only with the Oracle Database SQL query.\n
- **Do not provide any explanations, reasoning, or additional text.\n
- **Use only table names and columns present in the provided schema.\n
- **Ensure the SQL query adheres to	Oracle Database syntax.\n
- **Do not invent or assume table names or columns not provided in the schema.\n
- **Please use the most relevant table(s).\n
- **Please use table nam1e as mentioned in the schema.\n
- **Do not create sql queries for INSERT, UPDATE AND DELETE. Do not create any DDL Statements.\n
- **If the provided context is sufficient, please generate a valid Oracle SQL query without any explanations or reasoning for the question.\n
- **If the provided context is almost sufficient but requires knowledge of a specific string in a particular column, please generate an intermediate SQL query to find the distinct strings in that column. Prepend the query with a comment saying intermediate_sql.\n
- **If the question has been asked and answered before, please repeat the answer exactly as it was given before.\n\n
"""

SQL_RAG_FINAL_PROMPT_DUEX = """### Response:
   Based on your instructions, here is the sql query for the question `{question}` without any explanation:
   ```sql"""
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
