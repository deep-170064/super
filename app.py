import os
import logging
import shutil
import tempfile
import io
import zipfile

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import pandas as pd
import json
import uuid

from flask import jsonify
from sqlalchemy import text
from datetime import datetime
from flask_cors import CORS


# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


# Configure SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///supermarket.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Configure file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize SQLAlchemy with the app
db.init_app(app)

# Import models after db initialization to avoid circular imports
with app.app_context():
    import models
    db.create_all()

from api import api_bp

# Register blueprints
app.register_blueprint(api_bp, url_prefix='/api')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user doesn't select file, browser submits an empty file
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Generate a unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Store the file path in session for later use
            session['uploaded_file'] = file_path
            
            # Attempt to read and validate the file
            try:
                encoding = request.form.get('encoding', 'utf-8')
                df = pd.read_csv(file_path, encoding=encoding)
                
                # Check for required columns
                required_columns = ['Invoice ID', 'Date', 'Total', 'Quantity']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    flash(f"Warning: File is missing required columns: {', '.join(missing_columns)}", 'warning')
                
                # Store column info in session
                session['file_columns'] = df.columns.tolist()
                
                flash('File successfully uploaded!', 'success')
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                flash(f'Error reading file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('File type not allowed. Please upload a CSV file.', 'error')
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/dashboard')
def dashboard():
    if 'uploaded_file' not in session:
        flash('Please upload a file first', 'warning')
        return redirect(url_for('upload'))
    
    return render_template('dashboard.html')

@app.route('/analysis')
def analysis():
    if 'uploaded_file' not in session:
        flash('Please upload a file first', 'warning')
        return redirect(url_for('upload'))
    
    return render_template('analysis.html')

@app.route('/forecast')
def forecast():
    if 'uploaded_file' not in session:
        flash('Please upload a file first', 'warning')
        return redirect(url_for('upload'))
    
    return render_template('forecast.html')

@app.route('/streamlit')
def streamlit():
    # Provide a link to the Streamlit app
    streamlit_url = "https://supermarket-dashboardpbl.streamlit.app/"
    return redirect(streamlit_url)
@app.route('/db_health')
def db_health():
    try:
        # Try to execute a simple query
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            
        if result == 1:
            return jsonify({
                "status": "healthy",
                "message": "Database connection successful",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Database connection test returned unexpected result",
                "timestamp": datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Database connection error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/download-project')
def download_project():
    """
    Create a zip file containing the entire project with the correct structure
    and send it to the client for download.
    """
    try:
        # Create a temporary directory to organize files
        temp_dir = tempfile.mkdtemp()
        
        # Define the base directory structure
        project_dirs = [
            'templates',
            'static/css',
            'static/js',
            'static/assets',
            'uploads',
            'flask_api',
            'attached_assets'
        ]
        
        # Create the directory structure in the temp directory
        for directory in project_dirs:
            os.makedirs(os.path.join(temp_dir, directory), exist_ok=True)
        
        # List of Python files in the root directory to include
        root_py_files = [
            'app.py', 'main.py', 'models.py', 'api.py', 'config.py',
            'feature.py', 'visualise.py', 'utils.py', 'streamlit_app.py'
        ]
        
        # Copy the Python files to the temp directory
        for file in root_py_files:
            if os.path.exists(file):
                shutil.copy2(file, os.path.join(temp_dir, file))
        
        # Copy template files
        if os.path.exists('templates'):
            for template_file in os.listdir('templates'):
                if template_file.endswith('.html'):
                    shutil.copy2(
                        os.path.join('templates', template_file),
                        os.path.join(temp_dir, 'templates', template_file)
                    )
        
        # Copy static files
        if os.path.exists('static'):
            # CSS files
            if os.path.exists('static/css'):
                for css_file in os.listdir('static/css'):
                    if css_file.endswith('.css'):
                        shutil.copy2(
                            os.path.join('static/css', css_file),
                            os.path.join(temp_dir, 'static/css', css_file)
                        )
            
            # JS files
            if os.path.exists('static/js'):
                for js_file in os.listdir('static/js'):
                    if js_file.endswith('.js'):
                        shutil.copy2(
                            os.path.join('static/js', js_file),
                            os.path.join(temp_dir, 'static/js', js_file)
                        )
            
            # Asset files
            if os.path.exists('static/assets'):
                for asset_file in os.listdir('static/assets'):
                    shutil.copy2(
                        os.path.join('static/assets', asset_file),
                        os.path.join(temp_dir, 'static/assets', asset_file)
                    )
        
        # Copy flask_api files
        if os.path.exists('flask_api'):
            for api_file in os.listdir('flask_api'):
                if api_file.endswith('.py'):
                    shutil.copy2(
                        os.path.join('flask_api', api_file),
                        os.path.join(temp_dir, 'flask_api', api_file)
                    )
        
        # Copy attached_assets files
        if os.path.exists('attached_assets'):
            for asset_file in os.listdir('attached_assets'):
                if asset_file.endswith('.py'):
                    shutil.copy2(
                        os.path.join('attached_assets', asset_file),
                        os.path.join(temp_dir, 'attached_assets', asset_file)
                    )
        
        # Create a README.md file with setup instructions
        readme_content = """# Supermarket Sales Analytics Dashboard

## Project Structure
This project combines Flask, Streamlit, and JavaScript to create a comprehensive sales analytics dashboard.

## Setup Instructions
1. Install required packages: `pip install -r requirements.txt`
2. Set up the database: Make sure PostgreSQL is installed and configured
3. Run the Flask application: `python main.py`
4. Run the Streamlit application: `streamlit run streamlit_app.py`

## Features
- Data Visualization
- Customer Segmentation
- Sales Forecasting
- Advanced Analytics
"""
        
        with open(os.path.join(temp_dir, 'README.md'), 'w') as f:
            f.write(readme_content)
        
        # Create requirements.txt file
        requirements_content = """flask==2.3.3
flask-sqlalchemy==3.1.1
flask-login==0.6.3
pandas==2.2.3
numpy==2.2.0
plotly==6.0.0
seaborn==0.13.2
streamlit==1.45.0
prophet==1.1.6
scikit-learn==1.6.1
werkzeug==3.0.1
gunicorn==23.0.0
email-validator==2.1.1
psycopg2-binary==2.9.9
sqlalchemy==2.0.28
"""
        
        with open(os.path.join(temp_dir, 'requirements.txt'), 'w') as f:
            f.write(requirements_content)
        
        # Create a .env.example file with environment variables
        env_example_content = """# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/supermarket_db
PGHOST=localhost
PGPORT=5432
PGUSER=username
PGPASSWORD=password
PGDATABASE=supermarket_db

# Application Configuration
SESSION_SECRET=your_secret_key_here
STREAMLIT_URL=http://localhost:8501
"""
        
        with open(os.path.join(temp_dir, '.env.example'), 'w') as f:
            f.write(env_example_content)
        
        # Create zip file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Walk through the temp directory and add files to the zip
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zf.write(file_path, arcname)
        
        # Move to the beginning of the file
        memory_file.seek(0)
        
        # Clean up the temp directory
        shutil.rmtree(temp_dir)
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='supermarket_sales_dashboard.zip'
        )
    
    except Exception as e:
        logging.error(f"Error creating project download: {e}")
        flash(f"Error creating download: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True,use_reloader=False)

