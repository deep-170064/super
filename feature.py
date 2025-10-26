
import pandas as pd
import logging
import numpy as np
from prophet import Prophet
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_data(df):
    try:
        logging.info(f"Initial Data Shape: {df.shape}")
        df = df.drop_duplicates().ffill()
        logging.info(f"After Removing Duplicates: {df.shape}")
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['Day'] = df['Date'].dt.day_name()
        if 'Time' in df.columns and df['Time'].dtype == 'object':
            df['Hour'] = pd.to_datetime(df['Time'], errors='coerce').dt.hour

        return df
    except Exception as e:
        logging.error(f"Error in data cleaning: {e}")
        return pd.DataFrame()

def add_features(df):
    try:
        required_columns = ['Total', 'Quantity', 'Unit price']
        if all(col in df.columns for col in required_columns):
            df['Profit'] = df['Total'] - (df['Quantity'] * df['Unit price'])
            df['Profit Margin (%)'] = (df['Profit'] / df['Total']) * 100
            logging.info("Profit and Profit Margin calculated.")
        else:
            missing_cols = [col for col in required_columns if col not in df.columns]
            logging.warning(f"Missing columns for feature engineering: {missing_cols}")
        
        return df
    except Exception as e:
        logging.error(f"Error in feature engineering: {e}")
        return df

def customer_segmentation(df, n_clusters=3):
    """
    Perform K-Means clustering on key purchasing features to segment customers.
    Adds a 'Cluster' column to the DataFrame indicating each row's cluster assignment.
    
    :param df: DataFrame containing supermarket sales data
    :param n_clusters: Number of clusters to form (default is 3)
    :return: DataFrame with a new 'Cluster' column
    """
    try:
        required_cols = ['Total', 'Quantity', 'Unit price']
        if not all(col in df.columns for col in required_cols):
            logging.warning("Missing columns for segmentation. Segmentation skipped.")
            return df
        segmentation_df = df[required_cols].copy()
        segmentation_df = segmentation_df.dropna()
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(segmentation_df)
        kmeans = KMeans(n_clusters=n_clusters, init='k-means++', random_state=42)
        cluster_labels = kmeans.fit_predict(scaled_features)
        df.loc[segmentation_df.index, 'Cluster'] = cluster_labels
        
        logging.info(f"Customer Segmentation done with {n_clusters} clusters.")
        return df
    except Exception as e:
        logging.error(f"Error in customer segmentation: {e}")
        return df

def predict_sales_with_prophet(sales_data, periods=30, yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False):
    """
    Predict future sales using Facebook Prophet.
    
    Parameters:
    -----------
    sales_data : pandas.DataFrame
        DataFrame containing date column 'ds' and sales column 'y'
        (if your columns have different names, rename them before passing)
    periods : int, default=30
        Number of periods to forecast into the future
    yearly_seasonality : bool or int, default=True
        Whether to include yearly seasonality
    weekly_seasonality : bool or int, default=True
        Whether to include weekly seasonality
    daily_seasonality : bool or int, default=False
        Whether to include daily seasonality
        
    Returns:
    --------
    forecast : pandas.DataFrame
        DataFrame with the original data and forecast including:
        - ds: dates
        - y: actual values (where available)
        - yhat: predicted values
        - yhat_lower: lower bound of prediction interval
        - yhat_upper: upper bound of prediction interval
    model : Prophet model
        Trained Prophet model
    """
    df = sales_data.copy()
    if 'ds' not in df.columns or 'y' not in df.columns:
        raise ValueError("DataFrame must contain 'ds' (date) and 'y' (sales) columns")
    model = Prophet(
        yearly_seasonality=yearly_seasonality,
        weekly_seasonality=weekly_seasonality,
        daily_seasonality=daily_seasonality
    )
    model.fit(df)
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    forecast = pd.merge(forecast, df, on='ds', how='left')
    
    return forecast, model

def prepare_sales_data_for_prophet(df, date_column, sales_column):
    """
    Prepare sales data for Prophet by renaming columns to 'ds' and 'y'.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing sales data
    date_column : str
        Name of the column containing dates
    sales_column : str
        Name of the column containing sales values
        
    Returns:
    --------
    prophet_df : pandas.DataFrame
        DataFrame with columns renamed for Prophet
    """
    prophet_df = df.copy()
    prophet_df = prophet_df.rename(columns={date_column: 'ds', sales_column: 'y'})
    prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
    
    return prophet_df

def prepare_churn_data(df):
    try:
        if 'Date' not in df.columns or 'Total' not in df.columns or 'Quantity' not in df.columns:
            st.error("Missing required columns for churn prediction: 'Date', 'Total', 'Quantity'")
            return None, None

        # Ensure Date is in datetime format
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        # Remove invalid dates
        df = df.dropna(subset=['Date'])

        # Calculate features
        df['Days Since Last Purchase'] = (pd.to_datetime('today') - df['Date']).dt.days
        df['Average Purchase Value'] = df['Total'] / np.where(df['Quantity'] == 0, 1, df['Quantity'])

        # Handle missing or infinite values
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna()

        # Check for the Churn column
        if 'Churn' not in df.columns:
            # For demonstration, we'll define churn as customers who haven't purchased in 60+ days
            df['Churn'] = (df['Days Since Last Purchase'] > 60).astype(int)
        
        # Features and target
        X = df[['Total', 'Quantity', 'Average Purchase Value', 'Days Since Last Purchase']]
        y = df['Churn'].astype(int)
        return X, y
    except Exception as e:
        logging.error(f"Error preparing churn data: {e}")
        return None, None

def train_churn_model(X, y):
    try:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Optional Streamlit output if running in Streamlit environment
        if 'st' in globals():
            st.success(f"Churn Prediction Model Accuracy: {accuracy * 100:.2f}%")
        
        # Get feature importances for visualization
        feature_importances = model.feature_importances_
        feature_names = X.columns
        
        return {
            'model': model,
            'accuracy': float(accuracy),
            'features': list(feature_names),
            'importances': feature_importances.tolist(),
            'test_size': len(X_test),
            'churn_rate': float(y.mean())
        }
    except Exception as e:
        logging.error(f"Error training churn model: {e}")
        # Optional Streamlit output
        if 'st' in globals():
            st.error(f"Error training churn model: {e}")
        return None


def top_and_bottom_products(df, n=3):
    """
    Return the names of the top-n and bottom-n product lines by total sales.
    """
    cat_sales = df.groupby('Product line', observed=True)['Total'].sum()
    top = cat_sales.nlargest(n).index.tolist()      
    bottom = cat_sales.nsmallest(n).index.tolist()  
    return top, bottom

def sales_trend_changes(df):
    """
    Compute the week-over-week percentage change in total sales.
    """
    ts = df.set_index('Date').resample('W')['Total'].sum()
    pct_change = ts.pct_change().iloc[-1] * 100     
    return pct_change

def heatmap_peaks(df):
    """
    Find the single busiest (day, hour) and slowest (day, hour) periods.
    """
    import numpy as np
    
    # Ensure we have all required columns
    if 'Date' not in df.columns or 'Total' not in df.columns:
        return ('Unknown', 0), ('Unknown', 0)
    
    # Make a copy of the dataframe to avoid modifying the original
    data = df.copy()
    
    # Make sure Date is datetime
    if not pd.api.types.is_datetime64_any_dtype(data['Date']):
        try:
            data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        except Exception as e:
            logging.error(f"Error converting Date to datetime: {e}")
            return ('Unknown', 0), ('Unknown', 0)
    
    # Drop rows with NaT dates
    data = data.dropna(subset=['Date'])
    
    # If we have no data after cleaning, return defaults
    if data.empty:
        return ('Unknown', 0), ('Unknown', 0)
    
    try:
        # Extract day of week
        data['Day'] = data['Date'].dt.day_name()
        
        # If Time column exists, extract hour from it
        if 'Time' in data.columns:
            try:
                # Convert Time to datetime if it's a string
                if isinstance(data['Time'].iloc[0], str):
                    # Try different time formats
                    data['Hour'] = pd.to_datetime(data['Time'], format='%H:%M', errors='coerce').dt.hour
                    # If above fails, try another format
                    if data['Hour'].isna().all():
                        data['Hour'] = pd.to_datetime(data['Time'], errors='coerce').dt.hour
                else:
                    # If Time is already a datetime
                    data['Hour'] = data['Time'].dt.hour
            except Exception as e:
                logging.error(f"Error processing Time column: {e}")
                # Extract hour from Date as fallback
                data['Hour'] = data['Date'].dt.hour
        else:
            # If no Time column or Hour not already present
            if 'Hour' not in data.columns:
                data['Hour'] = data['Date'].dt.hour
            
        # Convert Hour to int to ensure proper grouping
        data['Hour'] = data['Hour'].fillna(0).astype(int)
        
        # Order days for proper sorting
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        data['Day'] = pd.Categorical(data['Day'], categories=day_order, ordered=True)
            
        # Group and aggregate - handle potential issues
        try:
            hm = data.groupby(['Day', 'Hour'], observed=True)['Total'].sum().reset_index()
            
            # If we have data in the aggregation
            if not hm.empty:
                busiest_idx = hm['Total'].idxmax()
                slowest_idx = hm['Total'].idxmin()
                
                busiest = (hm.loc[busiest_idx, 'Day'], int(hm.loc[busiest_idx, 'Hour']))
                slowest = (hm.loc[slowest_idx, 'Day'], int(hm.loc[slowest_idx, 'Hour']))
                
                return busiest, slowest
        except Exception as inner_e:
            logging.error(f"Error in aggregation: {inner_e}")
        
        # Fallback if the above fails
        return ('Unknown', 0), ('Unknown', 0)
            
    except Exception as e:
        logging.error(f"Error in heatmap_peaks: {e}")
        return ('Unknown', 0), ('Unknown', 0)

def correlation_insights(df, threshold=0.7):
    """
    Return list of variable pairs whose absolute correlation exceeds the threshold.
    """
    corr = df.select_dtypes(include='number').corr()
    strong = []
    for i in corr.columns:
        for j in corr.columns:
            if i != j and abs(corr.loc[i,j]) > threshold:
                strong.append((i, j, corr.loc[i,j]))
    return strong

def cluster_profiles(df):
    """
    Compute the average Total and Quantity for each cluster.
    """
    prof = df.groupby('Cluster', observed=True).agg({'Total':'mean','Quantity':'mean'}).round(2)
    return prof.to_dict('index')


def generate_advanced_suggestions(df, forecast_df=None):
    """
    Generate a list of actionable suggestions based on multiple insights:
      1. Top/bottom products
      2. Week-over-week sales change
      3. Heatmap peak/slow periods
      4. Strong correlations
      5. Cluster profiles
      6. Forecast warnings (optional)
      
    Parameters:
    -----------
    df : pandas.DataFrame
        The cleaned/filtered dataset, with columns Date, Total, Day, Hour, Cluster, etc.
    forecast_df : pandas.DataFrame, optional
        The Prophet forecast output with at least 'ds' and 'yhat' columns.
        
    Returns:
    --------
    suggestions : list of str
        A list of markdown-ready suggestion strings.
    """
    suggestions = []
    
    # Ensure Date is datetime
    if 'Date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # Top and bottom products
    if 'Product line' in df.columns and 'Total' in df.columns:
        try:
            top, bottom = top_and_bottom_products(df)
            suggestions.append(f"⭐ **Top-selling categories:** {', '.join(top)}. Consider expanding these lines.")
            suggestions.append(f"⚠️ **Low-performing categories:** {', '.join(bottom)}. Consider promotions or discounts.")    
        except Exception as e:
            logging.error(f"Error in top/bottom products: {e}")
    
    # Sales trend changes
    if 'Date' in df.columns and 'Total' in df.columns:
        try:
            change = sales_trend_changes(df)
            if change > 5:
                suggestions.append(f"📈 Sales are up **{change:.1f}%** week-over-week. Maintain current promotions.")
            elif change < -5:
                suggestions.append(f"📉 Sales are down **{abs(change):.1f}%** week-over-week. Investigate pricing or stock issues.")
        except Exception as e:
            logging.error(f"Error in sales trend changes: {e}")
            suggestions.append("ℹ️ Unable to compute week-over-week sales change.")
    
    # Heatmap peaks
    if 'Date' in df.columns and 'Total' in df.columns:
        try:
            busy, slow = heatmap_peaks(df)
            # Only add insights if we have valid data (not the default 'Unknown' values)
            if busy[0] != 'Unknown' and slow[0] != 'Unknown':
                suggestions.append(f"⏱️ **Busiest period:** {busy[0]} at {busy[1]}:00—ensure adequate staffing then.")
                suggestions.append(f"🐢 **Slowest period:** {slow[0]} at {slow[1]}:00—consider off-peak discounts.")
            else:
                suggestions.append("ℹ️ Insufficient time data to determine busiest/slowest periods.")
        except Exception as e:
            logging.error(f"Error in heatmap peaks: {e}")
            suggestions.append("ℹ️ Unable to determine busiest/slowest periods.")
    
    # Correlation insights
    try:
        # Select only numeric columns and drop columns with NaN values
        numeric_df = df.select_dtypes(include='number')
        
        # Filter out columns with all same values (which would have std dev = 0)
        valid_cols = [col for col in numeric_df.columns if numeric_df[col].std() > 0]
        
        if len(valid_cols) > 1:
            # Use only valid columns for correlation
            corr_raw = numeric_df[valid_cols].corr().fillna(0)  # Replace any NaN with 0
            
            pairs = []
            cols = corr_raw.columns
            for i in range(len(cols)):
                for j in range(i+1, len(cols)):
                    r = corr_raw.iloc[i, j]
                    
                    # Skip invalid correlation values
                    if pd.isna(r) or abs(r) < 0.1:
                        continue
                    
                    pairs.append((cols[i], cols[j], r))
            
            pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            
            if pairs:
                for a, b, r in pairs[:2]:
                    direction = "positively" if r > 0 else "negatively"
                    r_formatted = f"{r:.2f}"
                    suggestions.append(
                        f"🔗 **{a}** and **{b}** are {direction} correlated (r = {r_formatted}). "
                        "Consider exploring this relationship for deeper insights or targeted actions."
                    )
            else:
                suggestions.append("ℹ️ No significant correlations found between numeric variables.")
        else:
            suggestions.append("ℹ️ Insufficient numeric data for correlation analysis.")
    except Exception as e:
        logging.error(f"Error in correlation insights: {e}")
        suggestions.append(f"ℹ️ Correlation analysis failed: {str(e)}")
    
    # Cluster profiles
    if 'Cluster' in df.columns and 'Total' in df.columns and 'Quantity' in df.columns:
        try:
            profs = df.groupby('Cluster', observed=True).agg({'Total':'mean','Quantity':'mean'}).to_dict('index')
            for cl, m in profs.items():
                avg_spend, avg_qty = m['Total'], m['Quantity']
                if avg_spend > df['Total'].mean() * 1.2:
                    suggestions.append(
                        f"🎯 Cluster {cl} are your top spenders (avg ₹{avg_spend:.0f}). "
                        "Consider VIP loyalty rewards or exclusive previews."
                    )
                elif avg_qty < df['Quantity'].mean() * 0.8:
                    suggestions.append(
                        f"🛒 Cluster {cl} buys in small quantities (avg qty {avg_qty:.1f}). "
                        "Offer bundle deals or multi-buy discounts to increase basket size."
                    )
        except Exception as e:
            logging.error(f"Error in cluster profiles: {e}")
            suggestions.append("ℹ️ Cluster profiling ran but no targeted actions were generated.")
    
    # Forecast warnings
    if forecast_df is not None and 'yhat' in forecast_df.columns:
        try:
            threshold = forecast_df['yhat'].mean() * 0.8
            below_threshold = forecast_df[forecast_df['yhat'] < threshold]
            if len(below_threshold) > 0:
                dates = below_threshold['ds'].dt.strftime('%Y-%m-%d').tolist()[:3]
                suggestions.append(
                    f"📊 **Forecast alert:** Sales may drop below {threshold:.0f} on: {', '.join(dates)}... "
                    "Consider planning promotions for these periods."
                )
        except Exception as e:
            logging.error(f"Error in forecast warnings: {e}")
    
    return suggestions
