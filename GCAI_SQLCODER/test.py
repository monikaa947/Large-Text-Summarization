from utils.setup import run_sql_query
from utils.setup import setup_connexion
vn = setup_connexion()
# query = "SELECT journal_name, creation_date, created_by, journal_category, ledger_name, period_name FROM JOURNAL_DETAILS WHERE PERIOD_NAME=`23-Dec` AND PERIOD_STATUS = `U`"
# query = "select * from GL_JE_HEADERS"
# query = 'select * from GL_JE_HEADERS_NEW FETCH FIRST 5 ROWS ONLY;'

query = """SELECT db_name.name AS TABLE_CATALOG, table_cols.OWNER as TABLE_SCHEMA, table_cols.TABLE_NAME, table_cols.COLUMN_NAME, table_cols.DATA_TYPE
FROM v$database db_name
CROSS JOIN all_tab_cols table_cols
WHERE table_cols.OWNER = 'ADMIN' AND table_cols.TABLE_NAME in ('JOURNAL_DETAILS')"""
 
# query = "select * FROM margin_fact FETCH FIRST 5 ROWS ONLY;"
 
# query = "select * from gl_ledgers;"
 
df = run_sql_query(query)

# from dataclasses import dataclass
# from typing import Dict, List, Union

# @dataclass
# class TrainingPlanItem:
#     item_type: str
#     item_group: str
#     item_name: str
#     item_value: str

#     def __str__(self):
#         if self.item_type == self.ITEM_TYPE_SQL:
#             return f"Train on SQL: {self.item_group} {self.item_name}"
#         elif self.item_type == self.ITEM_TYPE_DDL:
#             return f"Train on DDL: {self.item_group} {self.item_name}"
#         elif self.item_type == self.ITEM_TYPE_IS:
#             return f"Train on Information Schema: {self.item_group} {self.item_name}"

#     ITEM_TYPE_SQL = "sql"
#     ITEM_TYPE_DDL = "ddl"
#     ITEM_TYPE_IS = "is"


# class TrainingPlan:
#     """
#     A class representing a training plan. You can see what's in it, and remove items from it that you don't want trained.

#     **Example:**
#     ```python
#     plan = vn.get_training_plan()

#     plan.get_summary()
#     ```

#     """

#     _plan: List[TrainingPlanItem]

#     def __init__(self, plan: List[TrainingPlanItem]):
#         self._plan = plan

#     def __str__(self):
#         return "\n".join(self.get_summary())

#     def __repr__(self):
#         return self.__str__()

#     def get_summary(self) -> List[str]:
#         """
#         **Example:**
#         ```python
#         plan = vn.get_training_plan()

#         plan.get_summary()
#         ```

#         Get a summary of the training plan.

#         Returns:
#             List[str]: A list of strings describing the training plan.
#         """

#         return [f"{item}" for item in self._plan]

#     def remove_item(self, item: str):
#         """
#         **Example:**
#         ```python
#         plan = vn.get_training_plan()

#         plan.remove_item("Train on SQL: What is the average salary of employees?")
#         ```

#         Remove an item from the training plan.

#         Args:
#             item (str): The item to remove.
#         """
#         for plan_item in self._plan:
#             if str(plan_item) == item:
#                 self._plan.remove(plan_item)
#                 break

# def get_training_plan_generic(df) -> TrainingPlan:
#         """
#         This method is used to generate a training plan from an information schema dataframe.

#         Basically what it does is breaks up INFORMATION_SCHEMA.COLUMNS into groups of table/column descriptions that can be used to pass to the LLM.

#         Args:
#             df (pd.DataFrame): The dataframe to generate the training plan from.

#         Returns:
#             TrainingPlan: The training plan.
#         """
#         # For each of the following, we look at the df columns to see if there's a match:
#         # database_column = df.columns[
#         #     df.columns.str.lower().str.contains("database")
#         #     | df.columns.str.lower().str.contains("table_catalog")
#         # ].to_list()[0]
#         # schema_column = df.columns[
#         #     df.columns.str.lower().str.contains("table_schema")
#         # ].to_list()[0]
#         table_column = df.columns[
#             df.columns.str.lower().str.contains("table_name")
#         ].to_list()[0]
#         columns = [
#             # database_column,
#             #         schema_column,
#                     table_column]
#         candidates = ["column_name",
#                       "data_type",
#                       "comment"]
#         matches = df.columns.str.lower().str.contains("|".join(candidates), regex=True)
#         columns += df.columns[matches].to_list()

#         plan = TrainingPlan([])

#         # for database in df[database_column].unique().tolist():
#         #     for schema in (
#         #         df.query(f'{database_column} == "{database}"')[schema_column]
#         #         .unique()
#         #         .tolist()
#         #     ):
#         for table in (
#             df[table_column]
#             .unique()
#             .tolist()
#         ):
#             df_columns_filtered_to_table = df.query(
#                 # f'{database_column} == "{database}" and {schema_column} == "{schema}" and {table_column} == "{table}"'
#                 f'{table_column} == "{table}"'
#             )
#             doc = f"The following columns are in the {table} table.\n\n"
#             doc += f"CREATE TABLE {table} ({','.join([' '.join(column_data) for column_data in df_columns_filtered_to_table[columns[1:]].values])})" #df_columns_filtered_to_table[columns].to_markdown()
#             plan._plan.append(
#                 TrainingPlanItem(
#                     item_type=TrainingPlanItem.ITEM_TYPE_IS,
#                     item_group=f"{'database'}.{'schema'}",
#                     item_name=table,
#                     item_value=doc,
#                 )
#             )

#         return plan
plan = vn.get_training_plan_generic(df)
print(plan._plan)
# # print(get_training_plan_generic())