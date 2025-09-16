import pandas as pd
from pandasql import sqldf


def load_data(file_path):
    """Loads data from an Excel file into a pandas DataFrame."""
    try:
        df = pd.read_excel(file_path)
        if 'Unnamed: 0' in df.columns:
            df = df.drop(columns=['Unnamed: 0'])
        return df, None
    except FileNotFoundError:
        return None, f"Error: The file '{file_path}' was not found."
    except Exception as e:
        return None, f"Error loading Excel file: {e}"

def get_dataframe_shape(df):
    """Returns the number of rows and columns of the DataFrame."""
    if df is not None:
        rows, cols = df.shape
        return f"The DataFrame has {rows} rows and {cols} columns."
    return "DataFrame is not loaded."

def get_column_statistics(df, column_name):
    """Provides descriptive statistics for a specified column."""
    if df is None:
        return "DataFrame is not loaded."
    if column_name not in df.columns:
        return f"Column '{column_name}' not found in the DataFrame."
    
    stats = df[column_name].describe()
    return stats.to_string()

def detect_outliers_iqr(df, column_name):
    """Detects outliers in a numerical column using the IQR method."""
    if df is None:
        return "DataFrame is not loaded."
    if column_name not in df.columns:
        return f"Column '{column_name}' not found in the DataFrame."

    if pd.api.types.is_numeric_dtype(df[column_name]):
        Q1 = df[column_name].quantile(0.25)
        Q3 = df[column_name].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = df[(df[column_name] < lower_bound) | (df[column_name] > upper_bound)]
        
        if not outliers.empty:
            return f" number of outliers detected in column '{column_name}' (IQR method):\n" + str(outliers.shape[0])
        else:
            return f"No outliers detected in column '{column_name}' (IQR method)."
    else:
        return f"Outlier detection (IQR method) is only applicable to numerical columns. '{column_name}' is not numerical."

def run_pandasql_query(query, df):
    """Runs a pandasql query on the DataFrame."""
    try:
        result = sqldf(query, {"df": df})
        return result, None
    except Exception as e:
        return None, f"Error running SQL query: {e}"
