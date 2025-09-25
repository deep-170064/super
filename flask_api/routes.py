import os
import pandas as pd
import numpy as np
import logging
import json
import tempfile
from flask import request, jsonify, send_file
from io import BytesIO

from flask_api.app import app
from flask_api.utils import process_sales_data, perform_customer_segmentation, generate_forecast, perform_churn_prediction

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/api/process_data', methods=['POST'])
def process_data():
    """Process uploaded sales data and return basic statistics"""
    try:
        # Check if file is in the request
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        encoding = request.form.get('encoding', 'utf-8')
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        # Read the file into a pandas DataFrame
        try:
            df = pd.read_csv(file, encoding=encoding)
        except UnicodeDecodeError:
            # Try alternative encoding if the specified one fails
            try:
                file.seek(0)
                df = pd.read_csv(file, encoding='latin1')
            except Exception as e:
                return jsonify({"error": f"Failed to read file: {str(e)}"}), 400
        
        # Process the data
        processed_data = process_sales_data(df)
        
        # Return basic stats about the data
        stats = {
            "rows": len(processed_data),
            "columns": list(processed_data.columns),
            "missing_values": processed_data.isna().sum().to_dict(),
            "summary": processed_data.describe().to_dict()
        }
        
        # Create a temporary file to save the processed data
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            processed_data.to_csv(tmp.name, index=False)
            tmp_filename = tmp.name
        
        return jsonify({
            "success": True,
            "stats": stats,
            "processed_file": os.path.basename(tmp_filename)
        })
    
    except Exception as e:
        logging.error(f"Error processing data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/customer_segmentation', methods=['POST'])
def customer_segmentation():
    """Perform customer segmentation on the processed data"""
    try:
        # Check if file is in the request
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        n_clusters = int(request.form.get('n_clusters', 3))
        
        # Read the data
        df = pd.read_csv(file)
        
        # Perform customer segmentation
        segmentation_results = perform_customer_segmentation(df, n_clusters)
        
        return jsonify({
            "success": True,
            "cluster_stats": segmentation_results["cluster_stats"],
            "cluster_profiles": segmentation_results["cluster_profiles"]
        })
    
    except Exception as e:
        logging.error(f"Error in customer segmentation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/forecast', methods=['POST'])
def forecast():
    """Generate sales forecast using Prophet"""
    try:
        # Check if file is in the request
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        periods = int(request.form.get('periods', 30))
        
        # Read the data
        df = pd.read_csv(file)
        
        # Generate forecast
        forecast_results = generate_forecast(df, periods)
        
        return jsonify({
            "success": True,
            "forecast": forecast_results["forecast"].to_dict(orient="records"),
            "components": forecast_results["components"].to_dict(orient="records") if "components" in forecast_results else None
        })
    
    except Exception as e:
        logging.error(f"Error generating forecast: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/churn_prediction', methods=['POST'])
def churn_prediction():
    """Perform churn prediction"""
    try:
        # Check if file is in the request
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        
        # Read the data
        df = pd.read_csv(file)
        
        # Perform churn prediction
        churn_results = perform_churn_prediction(df)
        
        return jsonify({
            "success": True,
            "churn_rate": churn_results["churn_rate"],
            "feature_importance": churn_results["feature_importance"],
            "at_risk_customers": churn_results["at_risk_customers"]
        })
    
    except Exception as e:
        logging.error(f"Error in churn prediction: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download processed file"""
    try:
        file_path = os.path.join(tempfile.gettempdir(), filename)
        return send_file(file_path, as_attachment=True, download_name="processed_data.csv")
    except Exception as e:
        logging.error(f"Error downloading file: {str(e)}")
        return jsonify({"error": str(e)}), 500
