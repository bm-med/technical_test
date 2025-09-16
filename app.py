import streamlit as st
from langchain_community.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI  # Updated import for ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import HumanMessage
from langchain.tools import Tool
from functools import partial

from utils import load_data, get_dataframe_shape, get_column_statistics, detect_outliers_iqr, run_pandasql_query

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Define Langchain Tools for function calling
tools = [
    Tool(
        name="get_dataframe_shape",
        func=get_dataframe_shape,
        description=(
            "Use ONLY if the user explicitly asks for the number of rows and columns "
            "and it cannot be answered with SQL. Otherwise, always use SQL."
        )
    ),
    Tool(
        name="get_column_statistics",
        func=get_column_statistics,
        description=(
            "Use ONLY if the question is about advanced statistics that cannot be expressed in SQL. "
            "For basic stats (count, nulls, min, max, mean, distinct, variance, stddev, etc.), "
            "always respond with a SQL query."
        )
    ),
    Tool(
        name="detect_outliers_iqr",
        func=detect_outliers_iqr,
        description=(
            "Detect outliers in a numerical column using the Interquartile Range (IQR) method. "
            "This cannot be done with SQL, so use this tool ONLY for outlier detection when the column is specified."
        )
    )
]


def main():
    st.set_page_config(page_title="Data Profiling Chatbot", layout="wide")
    st.title("📊 Data Profiling Chatbot with AI")

    # Re-added file uploader
    st.sidebar.header("Upload Data")
    uploaded_file = st.sidebar.file_uploader("Upload your Excel file", type=["xlsx"])

    df = None
    error_message = None
    if uploaded_file:
        with st.spinner("⏳ Connecting to database..."):
            df, error_message = load_data(uploaded_file)

    if error_message:
        st.error(f"❌ {error_message}")
    elif df is not None:
        st.sidebar.success(f"✅ Successfully connected to database.")
        st.sidebar.subheader("📊 Data Overview (First 5 Rows)")
        st.sidebar.dataframe(df.head())
        st.sidebar.subheader("Column Names:")
        st.sidebar.write(df.columns.tolist())

        st.markdown("--- ")
        st.subheader("💬 Ask a Question about your Data")

        user_question = st.text_area(
            "Enter your question here (e.g., 'How many rows are there?', 'What is the mean of the column X?', 'Are there any outliers in the X column?'):",
            height=100)

        if st.button("🔍 Get Answer"):
            if user_question:
                # Check if OpenAI API key is set
                if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"]:
                    st.warning("⚠️ Please set your OpenAI API key in the `.env` file or as an environment variable.")
                else:
                    with st.spinner("🧠 Generating response..."):
                        llm = ChatOpenAI(temperature=0, api_key=OPENAI_API_KEY, model="gpt-4o-mini")
                        columns_str = ", ".join(df.columns)

                        # Create Langchain Tools with bound functions
                        python_tools = [
                            Tool(name="get_dataframe_shape", func=lambda s: get_dataframe_shape(df),
                                 description="Get the number of rows and columns in the DataFrame. Input is ignored."),
                            Tool(name="get_column_statistics",
                                 func=lambda column_name: get_column_statistics(df, column_name),
                                 description="Get descriptive statistics for a specified column."),
                            Tool(name="detect_outliers_iqr",
                                 func=lambda column_name: detect_outliers_iqr(df, column_name),
                                 description="Detect outliers in a numerical column using the Interquartile Range (IQR) method."),
                        ]

                        # Agent creation
                        prompt = ChatPromptTemplate.from_messages([
                            ("system",
                             f"""You are a data analysis assistant. You always try to answer using SQL queries first.
                             The table name is 'df' and it has the following columns: {columns_str}.


                             Rules:
                             1. If the question can be answered with SQL, respond ONLY with a valid SQL query.
                             2. when generating SQL queries , Wrap each column name in backticks (`) to denote them as delimited identifiers.
                             2. For descriptive statistics of a column,
                                you MUST always respond with this SQL pattern (replace 'column_name' with the actual column name):

                                SELECT 
                                     COUNT(column_name) AS non_null_count,
                                     COUNT(*) - COUNT(column_name) AS null_count,
                                     MIN(column_name) AS min_value,
                                     MAX(column_name) AS max_value,
                                     AVG(column_name * 1.0) AS mean_value,
                                     SUM(column_name) AS total_value,
                                     COUNT(DISTINCT column_name) AS distinct_count
                                 FROM df;

                             3. For the min you can use :
                             SELECT MIN(column_name) from df;

                             4. For the max you can use :
                             SELECT MAX(column_name) from df;

                             5. If the user asks for a single value like mean, or average or sum or count generate an sql query for it.

                             6. For unique values, always use:
                                SELECT DISTINCT column_name FROM df;

                             7. For the number of rows and columns, always use:
                                SELECT 
                                    (SELECT COUNT(*) FROM df) AS row_count,
                                    (SELECT COUNT(*) FROM pragma_table_info('df')) AS column_count;


                             8. If the user asks about outliers:
                                - If a column name is provided, call the tool `detect_outliers_iqr`.
                                - If no column is specified, reply exactly with:
                                  "Please specify a column to detect outliers in."

                             9.  Never use Python tools for min, max, mean, nulls, distinct, or variance/stddev.
                                These must always be answered with SQL.

                             10. Only call the Python tool `detect_outliers_iqr` when SQL cannot handle the request.

                             Return NOTHING else besides either:
                             - a SQL query, or
                             - the exact tool response if needed.

                             11. If the user asks for statistics of a categorical (text/string) column, 
                             do NOT use MIN, MAX, or AVG. Instead, provide:
                             - Mode (most frequent value): 
                                 SELECT `column_name`, COUNT(*) AS frequency 
                                 FROM df 
                                 GROUP BY `column_name` 
                                 ORDER BY frequency DESC 
                                 LIMIT 1;

                             - Frequency distribution: 
                                 SELECT `column_name`, COUNT(*) AS frequency 
                                 FROM df 
                                 GROUP BY `column_name` 
                                 ORDER BY frequency DESC;

                             - Number of unique categories: 
                                 SELECT COUNT(DISTINCT `column_name`) AS distinct_count FROM df;

                             If the user asks for numerical statistics (AVG, MIN, MAX) on a categorical column, respond ONLY with the exact string 'Cannot process numerical statistics for categorical columns. Please specify a numerical column.'

                             """
                             ), MessagesPlaceholder("chat_history", optional=True), ("human", "{input}"), MessagesPlaceholder("agent_scratchpad"), ])

                        agent = create_openai_tools_agent(llm, python_tools, prompt)
                        agent_executor = AgentExecutor(agent=agent, tools=python_tools, verbose=True)

                        response = agent_executor.invoke({"input": user_question, "chat_history": []})

                        st.markdown("### ✨ Analysis Result")

                        # Handle SQL vs Tool/Text outputs
                        if isinstance(response, dict) and "output" in response:
                            final_response_content = response["output"]
                        elif hasattr(response, 'content'):
                            final_response_content = response.content
                        else:
                            final_response_content = str(response)

                        # Case 1: Outlier column missing
                        if final_response_content == "Please specify a column to detect outliers in.":
                            st.warning(f"⚠️ {final_response_content}")
                        elif final_response_content == "Cannot process numerical statistics for categorical columns. Please specify a numerical column.":
                            st.warning(f"⚠️ {final_response_content}")

                        # Case 2: SQL query → run it automatically
                        elif final_response_content.upper().startswith(
                                ("SELECT", "PRAGMA", "CREATE", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER")):
                            generated_sql = final_response_content
                            st.info("Generated SQL Query:")
                            st.code(generated_sql, language="sql")

                            with st.spinner("🚀 Running SQL query and fetching results..."):
                                result, sql_error_message = run_pandasql_query(generated_sql, df)
                                if sql_error_message:
                                    st.error(f"❌ {sql_error_message}")
                                elif result is not None:
                                    st.success("✅ Done!")
                                    st.dataframe(result)

                        # Case 3: Direct tool/text response
                        else:
                            st.write(final_response_content)

            else:
                st.warning("⚠️ Please enter a question.")
    else:
        st.info("⬆️ Please upload an Excel file to get started.")


if __name__ == "__main__":
    main()
