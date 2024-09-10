# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import os
import json
import logging
import argparse
from dotenv import load_dotenv
from utils.setup import setup_connexion
from utils.constants import LOG_FORMAT

load_dotenv()
logging.basicConfig(format=LOG_FORMAT,level=logging.DEBUG)
log = logging.getLogger(__name__)
vn = setup_connexion()


TABLE_NAMES = os.getenv("source_table_names")


# ++++++++++++++++++++ DO NOT RUN THE BELOW CODE AGAIN ++++++++++++++++++++++++++++++++++++
def training_schema_script():
    """
    The training_schema_script fetches metadata of the tables from the source database.\n
    The metadata is transformed to create training plan.\n
    The training plan is used to create meta data embeddings in the vector database.
    """
    df_information_schema = vn.run_sql(f"""SELECT 
                                            db_name.name AS TABLE_CATALOG, 
                                            table_cols.OWNER as TABLE_SCHEMA, 
                                            table_cols.TABLE_NAME, 
                                            table_cols.COLUMN_NAME, 
                                            table_cols.DATA_TYPE
                                          FROM 
                                            v$database db_name
                                          CROSS JOIN all_tab_cols table_cols
                                          WHERE 
                                            table_cols.OWNER = 'ADMIN' AND 
                                            table_cols.TABLE_NAME in ({TABLE_NAMES})""")
    # This will break up the information schema into bite-sized chunks that can be referenced by the LLM
    plan = vn.get_training_plan_generic(df=df_information_schema)
    log.debug(plan)
    vn.train(plan=plan)

# training_schema_script()

# def training_script():
#     vn.train(sql="""SELECT FINANCIAL.COST_CENTER, SUM(FINANCIAL.OPERATING_EXPENSES) AS CURRENT_YEAR_EXPENSE,
#               SUM(FINANCIAL.PREVIOUS_YEAR_OPERATING_EXPENSES) AS PREVIOUS_YEAR_EXPENSE 
#              FROM FINANCIAL 
#              GROUP BY FINANCIAL.COST_CENTER""",
#              question="How much is the expense compared to the previous year of all the departments?")
    
#     vn.train(sql="""SELECT FINANCIAL.COST_CENTER, FINANCIAL.ACCOUNT_GROUP,
#              SUM(FINANCIAL.REVENUE) / SUM(FINANCIAL.OPERATING_EXPENSES) AS REVENUE_TO_EXPENSE_RATIO
#              FROM FINANCIAL
#              GROUP BY FINANCIAL.COST_CENTER, FINANCIAL.ACCOUNT_GROUP
#              HAVING SUM(FINANCIAL.REVENUE) / SUM(FINANCIAL.OPERATING_EXPENSES) = 
#                 (SELECT MAX(SUM(FINANCIAL.REVENUE) / SUM(FINANCIAL.OPERATING_EXPENSES))
#                 FROM FINANCIAL
#                 GROUP BY FINANCIAL.COST_CENTER, FINANCIAL.ACCOUNT_GROUP)""",
#             question="which department had higher revenue to operating expense ratio?")
    
#     vn.train(sql="""SELECT REASON, AVG(AGE) AS AVERAGE_AGE, AVG(SALARY) AS AVERAGE_SALARY
#              FROM HR_LEAVERS 
#              GROUP BY REASON""",
#              question="For all the reasons of attritions what is the average age and salary breakdown?")
    
#     vn.train(sql="SELECT * FROM PAYROLL", question="Show salary data")

#     vn.train(sql="SELECT * FROM PERSONS", question="Show employee data")

#     vn.train(sql="""SELECT COST_CENTER, MAX(OPERATING_EXPENSES) as Max_Expense
#             FROM FINANCIAL
#             GROUP BY COST_CENTER""", question="How much is the maximum expense by various departments")

# training_script()

def train_existing_queries(data_file):
    """
    Train on exiting Question & SQL pair.
    arguments:
        data_file: A JSON file path which contains training data.
        JSON file should contain data in following format
        [
            [
                "0e18eb53-7c12-48c1-b8dc-fb198eeecda7-sql",
                "Show employee data",
                "SELECT * from employee",
                "sql"
            ],
            [
                "42d86575-3eee-4371-a93f-ae3aa272b857-sql",
                "Which team has the highest score?",
                "SELECT team_name, SUM(score) AS Highest_Score FROM dummy_team GROUP BY team_name ORDER BY Highest_Score DESC FETCH FIRST 1 ROW ONLY",
                "sql"
            ]
        ]
    return:
        None
    """ 
    
    # Load JSON data from file
    with open(data_file, 'r') as file:
        json_data = json.load(file)
        
        for item in json_data:
            if item[3] == "sql":
                log.info(f"Training {item}\n...")
                question = item[1]
                sql = item[2]
                vn.train(sql=sql, question=question)
            else:
                log.debug(f"Skipping item:\n{item}")


def untrain_examples(data_file):
    # Load JSON data from file
    with open(data_file, 'r') as file:
        json_data = json.load(file)
        
        for item in json_data:
            if item[3] == "sql":
                log.info(f"Processing {item}\n...")

                training_id = item[0]
                untrained = vn.remove_training_data(id=training_id)
                log.info(f"Untrained {item[0]}: {untrained}")
            else:
                log.debug(f"Skipping item:\n{item}")    
    

# train_existing_queries('training_data.json')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute functions based on command line arguments")
    parser.add_argument("action", choices=["train_db_schema", "train_examples", "untrain_all_examples"], help="As per the names, pass any one function argument to run the training.")
    parser.add_argument("--data-file", help="path for JSON file which contains the training examples data")

    args = parser.parse_args()

    if args.action == "train_db_schema":
        training_schema_script()
    elif args.action == "untrain_all_examples":
        untrain_examples(args.data_file)
    elif args.action == "train_examples":
        if not args.data_file:
            log.error("Error: data_file argument which is a JSON file containing training data, is required for training on existing queries")
        else:
            train_existing_queries(args.data_file)
