# Data Profiling Chatbot with AI

This project develops an interactive data profiling chatbot using Streamlit, Langchain, and Pandas, allowing non-technical users to query and analyze their data using natural language.

## Features

*   **Natural Language Queries**: Ask questions about your data in plain English.
*   **Langchain Function Calling**: Utilizes Langchain's robust function calling capabilities to intelligently choose between SQL queries and Python functions.
*   **SQL Generation**: Automatically converts natural language questions into SQL queries using `pandasql` for basic data retrieval and complex aggregations.
*   **Python Function Dispatch**: Handles complex data profiling tasks (e.g., shape, advanced statistics, outlier detection) by dispatching to dedicated Python functions.
*   **User File Upload**: Allows users to upload their own Excel files (`.xlsx`) for analysis.
*   **User-Friendly Interface**: An aesthetically pleasing Streamlit interface with clear visual cues and feedback.

## Project Structure

```
. # Project Root
├── app.py           # Main Streamlit application and Langchain agent setup
├── utils.py         # Utility functions for data loading, processing, and SQL execution
├── .env             # Environment variables (e.g., OPENAI_API_KEY)
├── requirements.txt # Python dependencies
└── <your_data_file>.xlsx # User-uploaded Excel data file
```

## Setup and Installation

Follow these steps to set up and run the application locally.

### 1. Clone the repository (if applicable)

If this project is in a repository, clone it to your local machine.

```bash
git clone <repository_url>
cd <project_directory>
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate # On macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**`requirements.txt` content:**

```
streamlit
pandas
openpyxl
pandasql
langchain
langchain-openai 
python-dotenv
```

### 4. Set up OpenAI API Key

Create a `.env` file in the root directory of your project (the same directory as `app.py` and `utils.py`) and add your OpenAI API key:

```
OPENAI_API_KEY="your_openai_api_key_here"
```

Replace `"your_openai_api_key_here"` with your actual OpenAI API key.

### 5. Prepare your data file

Ensure you have an Excel data file (`.xlsx`) ready for upload when you run the application. T
## How to Run the Application

Once you have completed the setup, run the Streamlit application from your terminal:

```bash
streamlit run app.py
```

This will open the application in your web browser.

## Usage

1.  On the Streamlit interface, use the sidebar to **upload your Excel data file**.
2.  Once the file is loaded, the sidebar will display a preview of the data.
3.  In the chat section, enter your natural language questions about the data.
4.  The chatbot will process your question, using either a generated SQL query or calling a relevant Python function, and display the results.

### Example Questions:

*   "How many rows and columns are there?"
*   "What are the statistics for the 'Salary' column?"
*   "Are there any outliers in the 'Age' column?"
*   "How many rows have 'City' as 'New York'?"
*   "What are the unique values in the 'Department' column?"
*   "What is the mean of the column `Transaction Value`?"
*   "Are there any outliers in my table?" (This will prompt you to specify a column)

## Customization

*   **Add More Python Functions**: You can extend `utils.py` with more complex data analysis functions and update the `tools` list and `system_prompt` in `app.py` to make the Langchain agent aware of them.
*   **Change LLM Model**: You can modify the `model` parameter in the `ChatOpenAI` initialization in `app.py` to use a different OpenAI model (e.g., `gpt-4`).
