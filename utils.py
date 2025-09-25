import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime

def validate_csv(file_path, required_columns=None):
    """
    Validate a CSV file by checking if it exists and contains the required columns.
    
    Parameters:
    -----------
    file_path : str
        Path to the CSV file
    required_columns : list, optional
        List of column names that must be present in the file
        
    Returns:
    --------
    dict
        Validation result with keys:
        - valid: bool, whether the file is valid
        - message: str, error message if invalid
        - columns: list, detected columns if valid
        - sample: DataFrame, sample of the data if valid
    """
    # Check if file exists
    if not os.path.exists(file_path):
        return {
            'valid': False,
            'message': f"File not found: {file_path}"
        }
    
    try:
        # Try multiple encodings
        encodings = ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252']
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, nrows=5)
                break
            except UnicodeDecodeError:
                continue
        else:
            return {
                'valid': False,
                'message': "Could not decode file with any of the attempted encodings"
            }
        
        # Check required columns
        if required_columns:
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return {
                    'valid': False,
                    'message': f"Missing required columns: {', '.join(missing_columns)}"
                }
        
        # Get full data for column info
        df_full = pd.read_csv(file_path, encoding=encoding)
        columns = df_full.columns.tolist()
        column_types = {col: str(df_full[col].dtype) for col in columns}
        
        # Return success
        return {
            'valid': True,
            'columns': columns,
            'column_types': column_types,
            'encoding': encoding,
            'sample': df.to_dict('records'),
            'row_count': len(df_full)
        }
    
    except Exception as e:
        return {
            'valid': False,
            'message': f"Error validating file: {str(e)}"
        }

def clean_and_prepare_data(df):
    """
    Clean and prepare a DataFrame for analysis.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The DataFrame to clean and prepare
        
    Returns:
    --------
    pandas.DataFrame
        The cleaned and prepared DataFrame
    """
    try:
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Fill missing values
        df = df.fillna(method='ffill')
        
        # Convert date columns
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['Day'] = df['Date'].dt.day_name()
            df['Month'] = df['Date'].dt.month_name()
            df['Year'] = df['Date'].dt.year
        
        # Convert time columns
        if 'Time' in df.columns:
            try:
                df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M', errors='coerce').dt.hour
            except:
                # Try to extract hour from the time string
                df['Hour'] = df['Time'].str.split(':', expand=True)[0].astype(int)
        
        # Add derived features if possible
        if all(col in df.columns for col in ['Total', 'Quantity', 'Unit price']):
            df['Average Item Price'] = df['Total'] / df['Quantity']
        
        return df
    
    except Exception as e:
        logging.error(f"Error in clean_and_prepare_data: {e}")
        return df  # Return original dataframe in case of error

def filter_dataframe(df, filters):
    """
    Filter a DataFrame based on provided filters.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The DataFrame to filter
    filters : dict
        Dictionary of filters to apply. Can include:
        - category: str, product category
        - customer_type: str, customer type
        - gender: str, gender
        - date_range: list, [start_date, end_date]
        
    Returns:
    --------
    pandas.DataFrame
        The filtered DataFrame
    """
    try:
        filtered_df = df.copy()
        
        # Product category filter
        if filters.get('category') and filters['category'] != 'All' and 'Product line' in df.columns:
            filtered_df = filtered_df[filtered_df['Product line'] == filters['category']]
        
        # Customer type filter
        if filters.get('customer_type') and filters['customer_type'] != 'All' and 'Customer type' in df.columns:
            filtered_df = filtered_df[filtered_df['Customer type'] == filters['customer_type']]
        
        # Gender filter
        if filters.get('gender') and filters['gender'] != 'All' and 'Gender' in df.columns:
            filtered_df = filtered_df[filtered_df['Gender'] == filters['gender']]
        
        # Date range filter
        if filters.get('date_range') and 'Date' in df.columns:
            start_date = pd.to_datetime(filters['date_range'][0])
            end_date = pd.to_datetime(filters['date_range'][1])
            filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]
        
        return filtered_df
    
    except Exception as e:
        logging.error(f"Error in filter_dataframe: {e}")
        return df  # Return original dataframe in case of error

def get_unique_values(df, column):
    """
    Get unique values for a specific column in a DataFrame.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The DataFrame to extract unique values from
    column : str
        The column name to get unique values for
        
    Returns:
    --------
    list
        List of unique values in the column
    """
    if column not in df.columns:
        return []
    
    unique_values = df[column].dropna().unique().tolist()
    return sorted(unique_values)
