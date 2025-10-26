import os
import json
import pandas as pd
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
import uuid
import logging
from feature import customer_segmentation, prepare_churn_data, train_churn_model, predict_sales_with_prophet, prepare_sales_data_for_prophet, generate_advanced_suggestions
from visualise import plot_prophet_forecast, plot_sales_heatmap, plot_category_sales, enable_data_download, sales_by_hour, sales_by_Time, sales_by_product_category, product_specific_analysis
import plotly

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

api_bp = Blueprint('api', __name__)

@api_bp.route('/load-data', methods=['GET'])
def load_data():
    """
    Load the data from the uploaded file in the session.
    Returns a sample of the data and column information.
    If no file is uploaded, returns sample data.
    """
    try:
        if 'uploaded_file' not in session:
            # Return sample data if no file is uploaded
            logging.info("No file in session - providing sample data")
            
            # Create sample data for demonstration (ensure all arrays are same length)
            n = 100
            invoice_ids = [f'INV-{i}' for i in range(1, n+1)]
            dates = pd.date_range(start='2023-01-01', periods=n).astype(str).tolist()
            # Generate times cycling through hours and minutes
            times = []
            for i in range(n):
                hour = 8 + (i % 12)  # hours from 8 to 19
                minute = (i * 5) % 60
                times.append(f"{hour}:{str(minute).zfill(2)}")

            totals = [round(100 + 900 * i / (n-1), 2) for i in range(n)]
            quantities = [i % 10 + 1 for i in range(n)]
            unit_prices = [round(10 + 90 * i / (n-1), 2) for i in range(n)]
            product_lines = (['Electronics', 'Food and beverages', 'Health and beauty', 'Sports and travel', 'Home and lifestyle'] * ((n // 5) + 1))[:n]
            payments = (['Cash', 'Credit card', 'Ewallet'] * ((n // 3) + 1))[:n]
            genders = (['Male', 'Female'] * ((n // 2) + 1))[:n]
            customer_types = (['Member', 'Normal'] * ((n // 2) + 1))[:n]

            data = {
                'Invoice ID': invoice_ids,
                'Date': dates,
                'Time': times,
                'Total': totals,
                'Quantity': quantities,
                'Unit price': unit_prices,
                'Product line': product_lines,
                'Payment': payments,
                'Gender': genders,
                'Customer type': customer_types
            }
            
            df = pd.DataFrame(data)
            
            # Save the sample data to a temporary file
            import tempfile
            import os
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
            temp_file_path = temp_file.name
            df.to_csv(temp_file_path, index=False)
            temp_file.close()
            
            # Store the file path in the session for future use
            session['uploaded_file'] = temp_file_path
            logging.info(f"Created temporary sample data file: {temp_file_path}")
            
            # Get column information
            columns = df.columns.tolist()
            column_types = {col: str(df[col].dtype) for col in columns}
            
            # Return only a sample of the data
            sample_data = df.head(50).to_dict('records')
            
            return jsonify({
                'success': True,
                'sample_data': sample_data,
                'columns': columns,
                'column_types': column_types,
                'row_count': len(df),
                'note': 'Using sample data. Upload a file for custom data analysis.'
            })
        
        # If a file is uploaded, process it
        file_path = session['uploaded_file']
        encoding = request.args.get('encoding', 'utf-8')
        
        df = pd.read_csv(file_path, encoding=encoding)
        
        # Clean the data
        df = df.drop_duplicates()
        # Use ffill() instead of deprecated fillna(method='ffill')
        df = df.ffill()
        
        # Convert date columns if present
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        # Get column information
        columns = df.columns.tolist()
        column_types = {col: str(df[col].dtype) for col in columns}
        
        # Return only a sample of the data to keep the response size small
        sample_data = df.head(50).to_dict('records')
        
        # Get summary statistics
        try:
            numeric_stats = df.describe().to_dict()
        except Exception as e:
            numeric_stats = {'error': str(e)}
        
        return jsonify({
            'success': True,
            'columns': columns,
            'column_types': column_types,
            'sample_data': sample_data,
            'numeric_stats': numeric_stats,
            'row_count': len(df)
        })
    
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/filter-data', methods=['POST'])
def filter_data():
    """
    Filter the data based on provided criteria.
    """
    try:
        if 'uploaded_file' not in session:
            logging.warning("No file in session for filtering - creating sample data")
            # Call load_data to create sample data
            return_value = load_data()
            if isinstance(return_value, tuple) and len(return_value) > 1 and return_value[1] != 200:
                return return_value
            
        file_path = session.get('uploaded_file')
        if not file_path or not os.path.exists(file_path):
            logging.warning(f"File in session does not exist: {file_path} - creating new sample data")
            # Call load_data to create new sample data
            return_value = load_data()
            if isinstance(return_value, tuple) and len(return_value) > 1 and return_value[1] != 200:
                return return_value
            file_path = session.get('uploaded_file')
        
        encoding = request.json.get('encoding', 'utf-8')
        
        # Load the data
        df = pd.read_csv(file_path, encoding=encoding)
        
        # Clean the data
        df = df.drop_duplicates()
        # Use ffill() instead of deprecated fillna(method='ffill')
        df = df.ffill()
        
        # Convert date columns if present
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Apply filters
        filters = request.json.get('filters', {})
        filtered_df = df.copy()
        
        # Log filter operation for debugging
        logging.info(f"Applying filters: {filters}")
        
        # Product category filter
        if 'category' in filters and filters['category'] != 'All' and 'Product line' in df.columns:
            filtered_df = filtered_df[filtered_df['Product line'] == filters['category']]
            logging.debug(f"After category filter - rows: {len(filtered_df)}")
        
        # Customer type filter
        if 'customer_type' in filters and filters['customer_type'] != 'All' and 'Customer type' in df.columns:
            filtered_df = filtered_df[filtered_df['Customer type'] == filters['customer_type']]
            logging.debug(f"After customer type filter - rows: {len(filtered_df)}")
        
        # Gender filter
        if 'gender' in filters and filters['gender'] != 'All' and 'Gender' in df.columns:
            filtered_df = filtered_df[filtered_df['Gender'] == filters['gender']]
            logging.debug(f"After gender filter - rows: {len(filtered_df)}")
        
        # Date range filter
        if 'date_range' in filters and filters['date_range'] and len(filters['date_range']) == 2 and 'Date' in df.columns:
            try:
                start_date = pd.to_datetime(filters['date_range'][0])
                end_date = pd.to_datetime(filters['date_range'][1])
                filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]
                logging.debug(f"After date range filter - rows: {len(filtered_df)}")
            except Exception as date_error:
                logging.error(f"Error applying date filter: {date_error}")
        
        # Convert dates back to string for JSON serialization
        if 'Date' in filtered_df.columns:
            filtered_df['Date'] = filtered_df['Date'].dt.strftime('%Y-%m-%d')
        
        # Return sample of filtered data
        sample_data = filtered_df.head(50).to_dict('records')
        
        logging.info(f"Filter complete - total: {len(df)} rows, filtered: {len(filtered_df)} rows")
        
        return jsonify({
            'success': True,
            'filtered_sample': sample_data,
            'filtered_row_count': len(filtered_df)
        })
    
    except Exception as e:
        logging.error(f"Error filtering data: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/generate-chart', methods=['POST'])
def generate_chart():
    """
    Generate a chart based on the requested chart type.
    Returns the chart data in a format suitable for Plotly.js.
    """
    if 'uploaded_file' not in session:
        return jsonify({'error': 'No file uploaded'}), 400
    
    try:
        file_path = session['uploaded_file']
        encoding = request.json.get('encoding', 'utf-8')
        chart_type = request.json.get('chart_type')
        filters = request.json.get('filters', {})
        
        # Load and filter the data
        df = pd.read_csv(file_path, encoding=encoding)
        df = df.drop_duplicates()
        # Use ffill() instead of deprecated fillna(method='ffill')
        df = df.ffill()
        
        # Convert Date column if present
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Apply filters
        filtered_df = df.copy()
        
        # Product category filter
        if 'category' in filters and filters['category'] != 'All' and 'Product line' in df.columns:
            filtered_df = filtered_df[filtered_df['Product line'] == filters['category']]
        
        # Customer type filter
        if 'customer_type' in filters and filters['customer_type'] != 'All' and 'Customer type' in df.columns:
            filtered_df = filtered_df[filtered_df['Customer type'] == filters['customer_type']]
        
        # Gender filter
        if 'gender' in filters and filters['gender'] != 'All' and 'Gender' in df.columns:
            filtered_df = filtered_df[filtered_df['Gender'] == filters['gender']]
        
        # Date range filter
        if 'date_range' in filters and 'Date' in df.columns:
            start_date = pd.to_datetime(filters['date_range'][0])
            end_date = pd.to_datetime(filters['date_range'][1])
            filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]
        
        # Generate chart based on chart_type
        if chart_type == 'category_sales':
            # Check if required columns exist
            if 'Product line' not in filtered_df.columns or 'Total' not in filtered_df.columns:
                return jsonify({'error': 'Required columns missing: Product line, Total'}), 400
            
            category_sales = filtered_df.groupby('Product line')['Total'].sum().reset_index()
            chart_data = {
                'x': category_sales['Product line'].tolist(),
                'y': category_sales['Total'].tolist(),
                'type': 'bar',
                'title': 'Sales by Product Category'
            }
        
        elif chart_type == 'payment_method':
            # Check if required columns exist
            if 'Payment' not in filtered_df.columns or 'Total' not in filtered_df.columns:
                return jsonify({'error': 'Required columns missing: Payment, Total'}), 400
            
            payment_sales = filtered_df.groupby('Payment')['Total'].sum().reset_index()
            chart_data = {
                'x': payment_sales['Payment'].tolist(),
                'y': payment_sales['Total'].tolist(),
                'type': 'bar',
                'title': 'Sales by Payment Method'
            }
        
        elif chart_type == 'gender_distribution':
            # Check if required columns exist
            if 'Gender' not in filtered_df.columns or 'Total' not in filtered_df.columns:
                return jsonify({'error': 'Required columns missing: Gender, Total'}), 400
            
            gender_sales = filtered_df.groupby('Gender')['Total'].sum().reset_index()
            chart_data = {
                'labels': gender_sales['Gender'].tolist(),
                'values': gender_sales['Total'].tolist(),
                'type': 'pie',
                'title': 'Sales by Gender'
            }
        
        elif chart_type == 'customer_type':
            # Check if required columns exist
            if 'Customer type' not in filtered_df.columns or 'Total' not in filtered_df.columns:
                return jsonify({'error': 'Required columns missing: Customer type, Total'}), 400
            
            customer_sales = filtered_df.groupby('Customer type')['Total'].sum().reset_index()
            chart_data = {
                'labels': customer_sales['Customer type'].tolist(),
                'values': customer_sales['Total'].tolist(),
                'type': 'pie',
                'title': 'Sales by Customer Type'
            }
        
        elif chart_type == 'time_series':
            # Check if required columns exist
            if 'Date' not in filtered_df.columns or 'Total' not in filtered_df.columns:
                return jsonify({'error': 'Required columns missing: Date, Total'}), 400
            
            # Group by date and sum the total sales
            daily_sales = filtered_df.groupby(filtered_df['Date'].dt.date)['Total'].sum().reset_index()
            daily_sales['Date'] = daily_sales['Date'].astype(str)
            
            chart_data = {
                'x': daily_sales['Date'].tolist(),
                'y': daily_sales['Total'].tolist(),
                'type': 'line',
                'title': 'Daily Sales Trend'
            }
        
        elif chart_type == 'sales_heatmap':
            # Check if required columns exist
            if 'Date' not in filtered_df.columns or 'Total' not in filtered_df.columns:
                return jsonify({'error': 'Required columns missing: Date, Total'}), 400
            
            # Add day of week
            filtered_df['Day'] = filtered_df['Date'].dt.day_name()
            
            # Add hour if not present
            if 'Hour' not in filtered_df.columns:
                if 'Time' in filtered_df.columns:
                    filtered_df['Hour'] = pd.to_datetime(filtered_df['Time']).dt.hour
                else:
                    filtered_df['Hour'] = filtered_df['Date'].dt.hour
            
            # Group by day and hour
            heatmap_data = filtered_df.groupby(['Day', 'Hour'])['Total'].sum().reset_index()
            
            # Convert to list of lists for heatmap
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            hours = list(range(24))
            
            # Create a 2D grid for the heatmap
            z = [[0 for _ in range(len(hours))] for _ in range(len(days))]
            
            # Fill in the grid with sales data
            for _, row in heatmap_data.iterrows():
                day_idx = days.index(row['Day']) if row['Day'] in days else -1
                hour_idx = int(row['Hour']) if 0 <= int(row['Hour']) < 24 else -1
                
                if day_idx >= 0 and hour_idx >= 0:
                    z[day_idx][hour_idx] = row['Total']
            
            chart_data = {
                'z': z,
                'x': hours,
                'y': days,
                'type': 'heatmap',
                'title': 'Sales Heatmap by Day and Hour'
            }
        
        elif chart_type == 'product_analysis':
            # Check if required columns exist
            if 'Product line' not in filtered_df.columns or 'Unit price' not in filtered_df.columns or 'Quantity' not in filtered_df.columns:
                return jsonify({'error': 'Required columns missing: Product line, Unit price, Quantity'}), 400
            
            # Calculate average unit price by product
            avg_price = filtered_df.groupby('Product line')['Unit price'].mean().reset_index()
            
            # Calculate quantity sold by product
            qty_sold = filtered_df.groupby('Product line')['Quantity'].sum().reset_index()
            
            chart_data = {
                'price': {
                    'x': avg_price['Product line'].tolist(),
                    'y': avg_price['Unit price'].tolist(),
                    'type': 'bar',
                    'title': 'Average Unit Price by Product Category'
                },
                'quantity': {
                    'x': qty_sold['Product line'].tolist(),
                    'y': qty_sold['Quantity'].tolist(),
                    'type': 'bar',
                    'title': 'Quantity Sold by Product Category'
                }
            }
        
        else:
            return jsonify({'error': f'Invalid chart type: {chart_type}'}), 400
        
        return jsonify({
            'success': True,
            'chart_data': chart_data
        })
    
    except Exception as e:
        logging.error(f"Error generating chart: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/customer-segmentation', methods=['POST'])
def perform_customer_segmentation():
    """
    Perform customer segmentation analysis and return the results.
    """
    try:
        if 'uploaded_file' not in session:
            logging.warning("No file in session for customer segmentation - creating sample data")
            # Call load_data to create sample data
            return_value = load_data()
            if isinstance(return_value, tuple) and len(return_value) > 1 and return_value[1] != 200:
                return return_value
            
        file_path = session.get('uploaded_file')
        if not file_path or not os.path.exists(file_path):
            logging.warning(f"File in session does not exist: {file_path} - creating new sample data")
            # Call load_data to create new sample data
            return_value = load_data()
            if isinstance(return_value, tuple) and len(return_value) > 1 and return_value[1] != 200:
                return return_value
            file_path = session.get('uploaded_file')
            
        encoding = request.json.get('encoding', 'utf-8')
        n_clusters = int(request.json.get('n_clusters', 3))
        
        # Get filters from request
        filters = request.json.get('filters', {})
        
        # Load and prepare the data
        df = pd.read_csv(file_path, encoding=encoding)
        df = df.drop_duplicates()
        # Use ffill() instead of deprecated fillna(method='ffill')
        df = df.ffill()
        
        # Apply filters
        logging.info(f"Applying filters to segmentation data: {filters}")
        if filters:
            # Category filter
            if 'category' in filters and filters['category'] != 'All' and 'Product line' in df.columns:
                df = df[df['Product line'] == filters['category']]
                
            # Customer type filter
            if 'customer_type' in filters and filters['customer_type'] != 'All' and 'Customer type' in df.columns:
                df = df[df['Customer type'] == filters['customer_type']]
            
            # Gender filter
            if 'gender' in filters and filters['gender'] != 'All' and 'Gender' in df.columns:
                df = df[df['Gender'] == filters['gender']]
                
            # Date range filter
            if 'date_range' in filters and len(filters['date_range']) == 2 and filters['date_range'][0] and filters['date_range'][1]:
                start_date = filters['date_range'][0]
                end_date = filters['date_range'][1]
                
                # Convert to datetime if not already
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        
        if df.empty:
            return jsonify({'error': 'No data left after applying filters'}), 400
        
        # Check if required columns exist
        required_cols = ['Total', 'Quantity', 'Unit price']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return jsonify({'error': f'Required columns missing: {", ".join(missing_cols)}'}), 400
        
        # Perform customer segmentation
        segmented_df = customer_segmentation(df, n_clusters=n_clusters)
        
        # Check if there's enough data for segmentation
        if segmented_df.empty or 'Cluster' not in segmented_df.columns:
            return jsonify({'error': 'Not enough data for meaningful segmentation'}), 400
            
        # Prepare the response
        try:
            cluster_stats = segmented_df.groupby('Cluster').agg({
                'Total': ['mean', 'sum', 'count'],
                'Quantity': ['mean', 'sum']
            }).reset_index()
            
            # Flatten the multi-index columns
            if isinstance(cluster_stats.columns, pd.MultiIndex):
                cluster_stats.columns = ['_'.join(col) if isinstance(col, tuple) else col for col in cluster_stats.columns.values]
            else:
                # If it's not a multi-index, keep the columns as is
                pass
        except Exception as e:
            logging.error(f"Error processing segmentation results: {e}")
            return jsonify({'error': f'Error processing segmentation results: {str(e)}'}), 500
        
        # Convert to list of dicts for JSON response
        # Frontend expects the cluster id field to be named 'Cluster_' (see static/js/charts.js)
        # ensure the column name matches that expectation
        if 'Cluster' in cluster_stats.columns:
            cluster_stats = cluster_stats.rename(columns={'Cluster': 'Cluster_'})

        clusters = cluster_stats.to_dict('records')
        
        return jsonify({
            'success': True,
            'clusters': clusters,
            'n_clusters': n_clusters
        })
    
    except Exception as e:
        logging.error(f"Error performing customer segmentation: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sales-forecast', methods=['POST'])
def forecast_sales():
    """
    Generate a sales forecast using Prophet.
    """
    try:
        if 'uploaded_file' not in session:
            logging.warning("No file in session for sales forecast - creating sample data")
            # Call load_data to create sample data
            return_value = load_data()
            if isinstance(return_value, tuple) and len(return_value) > 1 and return_value[1] != 200:
                return return_value
            
        file_path = session.get('uploaded_file')
        if not file_path or not os.path.exists(file_path):
            logging.warning(f"File in session does not exist: {file_path} - creating new sample data")
            # Call load_data to create new sample data
            return_value = load_data()
            if isinstance(return_value, tuple) and len(return_value) > 1 and return_value[1] != 200:
                return return_value
            file_path = session.get('uploaded_file')
            
        encoding = request.json.get('encoding', 'utf-8')
        forecast_periods = int(request.json.get('periods', 30))
        
        # Get filters from request
        filters = request.json.get('filters', {})
        
        # Load and prepare the data
        df = pd.read_csv(file_path, encoding=encoding)
        
        # Check if required columns exist
        if 'Date' not in df.columns or 'Total' not in df.columns:
            return jsonify({'error': 'Required columns missing: Date, Total'}), 400
            
        # Apply filters
        logging.info(f"Applying filters to forecast data: {filters}")
        if filters:
            # Category filter
            if 'category' in filters and filters['category'] != 'All' and 'Product line' in df.columns:
                df = df[df['Product line'] == filters['category']]
                
            # Customer type filter
            if 'customer_type' in filters and filters['customer_type'] != 'All' and 'Customer type' in df.columns:
                df = df[df['Customer type'] == filters['customer_type']]
                
            # Date range filter
            if 'date_range' in filters and len(filters['date_range']) == 2 and filters['date_range'][0] and filters['date_range'][1]:
                start_date = filters['date_range'][0]
                end_date = filters['date_range'][1]
                
                # Convert to datetime
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        
        if df.empty:
            return jsonify({'error': 'No data left after applying filters'}), 400
            
        # Prepare data for Prophet
        prophet_df = prepare_sales_data_for_prophet(df, 'Date', 'Total')
        
        # Generate forecast
        forecast, model = predict_sales_with_prophet(
            prophet_df, 
            periods=forecast_periods,
            yearly_seasonality=True,
            weekly_seasonality=True
        )
        
        # Prepare data for the response
        forecast_data = {
            'ds': forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'y': forecast['y'].fillna(0).tolist(),
            'yhat': forecast['yhat'].tolist(),
            'yhat_lower': forecast['yhat_lower'].tolist(),
            'yhat_upper': forecast['yhat_upper'].tolist()
        }
        
        # Get components for additional plots if available
        try:
            components = model.plot_components(forecast)
            components_data = {
                'trend': {
                    'x': forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
                    'y': forecast['trend'].tolist(),
                    'name': 'Trend'
                },
                'weekly': {
                    'x': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                    'y': model.weekly_seasonality.tolist() if hasattr(model, 'weekly_seasonality') else [],
                    'name': 'Weekly Seasonality'
                },
                'yearly': {
                    'x': list(range(1, 13)),  # Months 1-12
                    'y': model.yearly_seasonality.tolist() if hasattr(model, 'yearly_seasonality') else [],
                    'name': 'Yearly Seasonality'
                }
            }
        except Exception as e:
            logging.warning(f"Could not generate component plots: {e}")
            components_data = {}
        
        return jsonify({
            'success': True,
            'forecast': forecast_data,
            'components': components_data,
            'periods': forecast_periods
        })
    
    except Exception as e:
        logging.error(f"Error generating sales forecast: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/churn-prediction', methods=['POST'])
def predict_churn():
    """
    Perform customer churn prediction analysis and return the results.
    """
    try:
        if 'uploaded_file' not in session:
            logging.warning("No file in session for churn prediction - creating sample data")
            # Call load_data to create sample data
            return_value = load_data()
            if isinstance(return_value, tuple) and len(return_value) > 1 and return_value[1] != 200:
                return return_value
            
        file_path = session.get('uploaded_file')
        if not file_path or not os.path.exists(file_path):
            logging.warning(f"File in session does not exist: {file_path} - creating new sample data")
            # Call load_data to create new sample data
            return_value = load_data()
            if isinstance(return_value, tuple) and len(return_value) > 1 and return_value[1] != 200:
                return return_value
            file_path = session.get('uploaded_file')
            
        encoding = request.json.get('encoding', 'utf-8')
        
        # Get filters from request
        filters = request.json.get('filters', {})
        
        # Load and prepare the data
        df = pd.read_csv(file_path, encoding=encoding)
        df = df.drop_duplicates()
        
        # Use ffill() instead of deprecated fillna(method='ffill')
        df = df.ffill()
        
        # Apply filters
        logging.info(f"Applying filters to churn prediction data: {filters}")
        if filters:
            # Category filter
            if 'category' in filters and filters['category'] != 'All' and 'Product line' in df.columns:
                df = df[df['Product line'] == filters['category']]
                
            # Customer type filter
            if 'customer_type' in filters and filters['customer_type'] != 'All' and 'Customer type' in df.columns:
                df = df[df['Customer type'] == filters['customer_type']]
            
            # Gender filter
            if 'gender' in filters and filters['gender'] != 'All' and 'Gender' in df.columns:
                df = df[df['Gender'] == filters['gender']]
                
            # Date range filter
            if 'date_range' in filters and len(filters['date_range']) == 2 and filters['date_range'][0] and filters['date_range'][1]:
                start_date = filters['date_range'][0]
                end_date = filters['date_range'][1]
                
                # Convert to datetime if not already
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        
        if df.empty:
            return jsonify({'error': 'No data left after applying filters'}), 400
            
        # Convert date columns
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
        # Prepare data for churn prediction
        X, y = prepare_churn_data(df)
        
        if X is None or y is None:
            return jsonify({'error': 'Could not prepare data for churn prediction'}), 500
            
        # Train model
        result = train_churn_model(X, y)
        
        if result is None:
            return jsonify({'error': 'Error training churn model'}), 500
            
        # Convert scikit-learn model to simple statistics
        result.pop('model', None)  # Remove the actual model object as it's not JSON serializable
        
        # Add additional metrics for the frontend
        result['churn_count'] = int(y.sum())
        result['total_customers'] = len(y)
        result['retention_rate'] = 1.0 - result['churn_rate']
        
        return jsonify({
            'success': True,
            'churn_data': result
        })
        
    except Exception as e:
        logging.error(f"Error in churn prediction: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/generate-insights', methods=['GET', 'POST'])
def generate_insights():
    """
    Generate advanced business insights and suggestions.
    """
    try:
        if 'uploaded_file' not in session:
            logging.warning("No file in session for business insights - creating sample data")
            # Call load_data to create sample data
            return_value = load_data()
            if isinstance(return_value, tuple) and len(return_value) > 1 and return_value[1] != 200:
                return return_value
            
        file_path = session.get('uploaded_file')
        if not file_path or not os.path.exists(file_path):
            logging.warning(f"File in session does not exist: {file_path} - creating new sample data")
            # Call load_data to create new sample data
            return_value = load_data()
            if isinstance(return_value, tuple) and len(return_value) > 1 and return_value[1] != 200:
                return return_value
            file_path = session.get('uploaded_file')
        
        # Use request.json for POST requests and request.args for GET requests
        encoding = request.args.get('encoding', 'utf-8') if request.method == 'GET' else request.json.get('encoding', 'utf-8')
        
        # Get filters from request
        filters = request.args.get('filters', {}) if request.method == 'GET' else request.json.get('filters', {})
        
        # Load the data
        df = pd.read_csv(file_path, encoding=encoding)
        df = df.drop_duplicates()
        # Use ffill() instead of deprecated fillna(method='ffill')
        df = df.ffill()
        
        # Apply filters
        logging.info(f"Applying filters to insights data: {filters}")
        if filters:
            # Category filter
            if 'category' in filters and filters['category'] != 'All' and 'Product line' in df.columns:
                df = df[df['Product line'] == filters['category']]
                
            # Customer type filter
            if 'customer_type' in filters and filters['customer_type'] != 'All' and 'Customer type' in df.columns:
                df = df[df['Customer type'] == filters['customer_type']]
            
            # Gender filter
            if 'gender' in filters and filters['gender'] != 'All' and 'Gender' in df.columns:
                df = df[df['Gender'] == filters['gender']]
                
            # Date range filter
            if 'date_range' in filters and len(filters['date_range']) == 2 and filters['date_range'][0] and filters['date_range'][1]:
                start_date = filters['date_range'][0]
                end_date = filters['date_range'][1]
                
                # Convert to datetime if not already
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        
        if df.empty:
            return jsonify({'error': 'No data left after applying filters'}), 400
        
        # Convert date columns if present
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Generate insights
        suggestions = generate_advanced_suggestions(df)
        
        return jsonify({
            'success': True,
            'insights': suggestions
        })
    
    except Exception as e:
        logging.error(f"Error generating insights: {e}")
        return jsonify({'error': str(e)}), 500
