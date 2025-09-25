import pandas as pd
import numpy as np
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from prophet import Prophet

def process_sales_data(df):
    """
    Process and clean the sales data
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The raw sales data
        
    Returns:
    --------
    pandas.DataFrame
        The processed sales data
    """
    try:
        # Make a copy to avoid modifying the original
        processed_df = df.copy()
        
        # Remove duplicates
        processed_df = processed_df.drop_duplicates()
        
        # Convert date column to datetime if it exists
        if 'Date' in processed_df.columns:
            processed_df['Date'] = pd.to_datetime(processed_df['Date'], errors='coerce')
            
            # Extract date components
            processed_df['Day'] = processed_df['Date'].dt.day_name()
            processed_df['Month'] = processed_df['Date'].dt.month_name()
            processed_df['Year'] = processed_df['Date'].dt.year
            
        # Convert time column to hour if it exists
        if 'Time' in processed_df.columns:
            try:
                processed_df['Hour'] = pd.to_datetime(processed_df['Time'], format='%H:%M', errors='coerce').dt.hour
            except Exception:
                # If standard conversion fails, try alternative approach
                processed_df['Hour'] = processed_df['Time'].str.split(':').str[0].astype(float)
        
        # Handle missing values
        numeric_cols = processed_df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            processed_df[col] = processed_df[col].fillna(processed_df[col].median())
        
        # Fill categorical with mode
        categorical_cols = processed_df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            processed_df[col] = processed_df[col].fillna(processed_df[col].mode()[0])
        
        # Calculate additional features if possible
        if all(col in processed_df.columns for col in ['Total', 'Quantity', 'Unit price']):
            # Calculate profit assuming a markup
            processed_df['Profit'] = processed_df['Total'] - (processed_df['Quantity'] * processed_df['Unit price'])
            processed_df['Profit Margin (%)'] = (processed_df['Profit'] / processed_df['Total']) * 100
            
        return processed_df
        
    except Exception as e:
        logging.error(f"Error processing sales data: {str(e)}")
        raise

def perform_customer_segmentation(df, n_clusters=3):
    """
    Perform K-means clustering for customer segmentation
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The processed sales data
    n_clusters : int
        The number of clusters to form
        
    Returns:
    --------
    dict
        Dictionary with segmentation results
    """
    try:
        required_cols = ['Total', 'Quantity']
        
        # Check if required columns are available
        if not all(col in df.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in df.columns]
            raise ValueError(f"Missing required columns for segmentation: {missing_cols}")
        
        # Prepare data for clustering
        features = []
        
        # Add spending features
        if 'Total' in df.columns:
            features.append('Total')
        
        # Add quantity features
        if 'Quantity' in df.columns:
            features.append('Quantity')
            
        # Add profit features if available
        if 'Profit' in df.columns:
            features.append('Profit')
        
        if 'Profit Margin (%)' in df.columns:
            features.append('Profit Margin (%)')
            
        # Check if we have enough features
        if len(features) < 2:
            raise ValueError("Not enough features for clustering")
            
        # Prepare the segmentation DataFrame
        segmentation_df = df[features].copy()
        segmentation_df = segmentation_df.dropna()
        
        # Standardize the features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(segmentation_df)
        
        # Perform K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, init='k-means++', random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(scaled_features)
        
        # Add cluster labels to the original DataFrame
        df_with_clusters = df.copy()
        df_with_clusters.loc[segmentation_df.index, 'Cluster'] = cluster_labels
        
        # Calculate cluster statistics
        cluster_stats = df_with_clusters.groupby('Cluster').agg({
            'Total': ['mean', 'min', 'max', 'count'],
            'Quantity': ['mean', 'min', 'max']
        }).reset_index()
        
        # Make column names more readable
        cluster_stats.columns = ['Cluster', 'Avg_Total', 'Min_Total', 'Max_Total', 'Count', 'Avg_Quantity', 'Min_Quantity', 'Max_Quantity']
        
        # Create cluster profiles
        cluster_profiles = {}
        for cluster in range(n_clusters):
            profile = {}
            cluster_data = df_with_clusters[df_with_clusters['Cluster'] == cluster]
            
            # Calculate common characteristics
            if 'Gender' in df_with_clusters.columns:
                profile['Dominant_Gender'] = cluster_data['Gender'].mode()[0]
                profile['Gender_Ratio'] = cluster_data['Gender'].value_counts(normalize=True).to_dict()
                
            if 'Customer type' in df_with_clusters.columns:
                profile['Dominant_Customer_Type'] = cluster_data['Customer type'].mode()[0]
                profile['Customer_Type_Ratio'] = cluster_data['Customer type'].value_counts(normalize=True).to_dict()
                
            if 'Product line' in df_with_clusters.columns:
                profile['Top_Products'] = cluster_data['Product line'].value_counts().nlargest(3).to_dict()
                
            if 'Payment' in df_with_clusters.columns:
                profile['Preferred_Payment'] = cluster_data['Payment'].mode()[0]
                
            # Add the profile to the cluster profiles
            cluster_profiles[int(cluster)] = profile
        
        return {
            "df_with_clusters": df_with_clusters,
            "cluster_stats": cluster_stats.to_dict(orient='records'),
            "cluster_profiles": cluster_profiles
        }
        
    except Exception as e:
        logging.error(f"Error in customer segmentation: {str(e)}")
        raise

def generate_forecast(df, periods=30):
    """
    Generate sales forecast using Prophet
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The processed sales data
    periods : int
        Number of periods to forecast into the future
        
    Returns:
    --------
    dict
        Dictionary with forecast results
    """
    try:
        # Check if required columns are available
        if 'Date' not in df.columns or 'Total' not in df.columns:
            raise ValueError("Missing required columns for forecasting: 'Date' and/or 'Total'")
        
        # Prepare data for Prophet
        prophet_df = df.copy()
        prophet_df['ds'] = pd.to_datetime(prophet_df['Date'])
        prophet_df['y'] = prophet_df['Total']
        
        # Aggregate by date (day)
        prophet_df = prophet_df.groupby('ds')['y'].sum().reset_index()
        
        # Initialize and fit Prophet model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )
        
        # Add custom seasonality if data spans more than 2 months
        if (prophet_df['ds'].max() - prophet_df['ds'].min()).days > 60:
            model.add_seasonality(
                name='monthly',
                period=30.5,
                fourier_order=5
            )
        
        model.fit(prophet_df)
        
        # Make future dataframe
        future = model.make_future_dataframe(periods=periods)
        
        # Forecast
        forecast = model.predict(future)
        
        # Get components
        components = model.plot_components(forecast)
        components_df = pd.DataFrame({
            'ds': forecast['ds'],
            'trend': forecast['trend'],
            'weekly': forecast['weekly'] if 'weekly' in forecast.columns else None,
            'yearly': forecast['yearly'] if 'yearly' in forecast.columns else None
        })
        
        # Merge forecast with actual values
        forecast = pd.merge(forecast, prophet_df, on='ds', how='left')
        
        return {
            "forecast": forecast,
            "components": components_df
        }
        
    except Exception as e:
        logging.error(f"Error generating forecast: {str(e)}")
        raise

def perform_churn_prediction(df):
    """
    Perform customer churn prediction
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The processed sales data
        
    Returns:
    --------
    dict
        Dictionary with churn prediction results
    """
    try:
        # Check if we have required data for churn prediction
        if 'Invoice ID' not in df.columns or 'Date' not in df.columns:
            raise ValueError("Missing required columns for churn prediction")
        
        # Convert date to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Create customer features
        customer_data = df.groupby('Invoice ID').agg({
            'Date': ['min', 'max', 'count'],
            'Total': ['sum', 'mean'],
            'Quantity': ['sum', 'mean']
        })
        
        # Flatten multi-index
        customer_data.columns = ['_'.join(col).strip() for col in customer_data.columns.values]
        customer_data = customer_data.reset_index()
        
        # Calculate days since first and last purchase
        today = pd.Timestamp.now()
        customer_data['days_since_first'] = (today - customer_data['Date_min']).dt.days
        customer_data['days_since_last'] = (today - customer_data['Date_max']).dt.days
        
        # Calculate purchase frequency (in days)
        customer_data['purchase_frequency'] = customer_data['days_since_first'] / np.maximum(customer_data['Date_count'], 1)
        
        # Define churn (example: customers who haven't purchased in the last 30 days)
        threshold = 30  # Can be adjusted based on business rules
        customer_data['churn'] = (customer_data['days_since_last'] > threshold).astype(int)
        
        # Select features for the model
        features = ['Total_sum', 'Total_mean', 'Quantity_sum', 'Quantity_mean', 
                   'days_since_first', 'days_since_last', 'purchase_frequency']
        
        X = customer_data[features]
        y = customer_data['churn']
        
        # Split data for training and evaluation
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        
        # Train a Random Forest classifier
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Evaluate model
        accuracy = np.mean(y_pred == y_test)
        
        # Get feature importance
        feature_importance = dict(zip(features, model.feature_importances_))
        
        # Identify customers at risk of churning
        customer_data['churn_probability'] = model.predict_proba(X)[:, 1]
        at_risk = customer_data[customer_data['churn_probability'] > 0.7]
        
        # Calculate overall churn rate
        churn_rate = customer_data['churn'].mean() * 100
        
        return {
            "churn_rate": churn_rate,
            "feature_importance": feature_importance,
            "at_risk_customers": at_risk[['Invoice ID', 'churn_probability', 'days_since_last', 'Total_sum']].to_dict(orient='records'),
            "accuracy": accuracy
        }
        
    except Exception as e:
        logging.error(f"Error in churn prediction: {str(e)}")
        raise
