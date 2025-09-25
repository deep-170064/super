
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import seaborn as sns
import plotly.figure_factory as ff
import os
import requests
from feature import customer_segmentation, prepare_churn_data, train_churn_model, predict_sales_with_prophet, prepare_sales_data_for_prophet, generate_advanced_suggestions
from visualise import plot_prophet_forecast, plot_sales_heatmap, plot_category_sales, enable_data_download, sales_by_hour, sales_by_Time, sales_by_product_category, product_specific_analysis, plot_correlation_matrix, plot_customer_segments, plot_payment_distribution

# Set page config
st.set_page_config(
    page_title="Supermarket Sales Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# No longer using Flask API

# Page title and intro
st.title("Supermarket Sales Dashboard")
st.markdown("""
This dashboard provides comprehensive analytics for supermarket sales data. 
Upload your CSV file to get started with data visualization, customer segmentation, and sales forecasting.
""")

# Sidebar for file upload and filters
st.sidebar.header("File Upload")

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'filtered_data' not in st.session_state:
    st.session_state.filtered_data = None
if 'file_path' not in st.session_state:
    st.session_state.file_path = None
if 'encodings' not in st.session_state:
    st.session_state.encodings = ["utf-8", "latin1", "ISO-8859-1", "cp1252"]

# Function to check required columns
def check_required_columns(df):
    required_columns = {
        'Product line': ['Sales by Product Category', 'Category Sales Analysis'],
        'Payment': ['Payment Method Analysis'],
        'Gender': ['Demographic Analysis'],
        'Customer type': ['Customer Type Analysis'],
        'Date': ['Time-based Analysis', 'Sales Forecast', 'Sales Heatmap'],
        'Total': ['Sales Analysis', 'Correlation Analysis', 'Forecasting'],
        'Quantity': ['Product Analysis', 'Correlation Analysis'],
        'Invoice ID': ['Customer Segmentation', 'Churn Prediction']
    }
    
    missing_columns = []
    affected_visualizations = []
    for col, visualizations in required_columns.items():
        if col not in df.columns:
            missing_columns.append(col)
            affected_visualizations.extend(visualizations)
    
    if missing_columns:
        st.warning("⚠️ Some columns are missing from your dataset:")
        for col in missing_columns:
            st.write(f"- Missing '{col}' column")
        
        st.warning("The following visualizations may not work properly:")
        for viz in set(affected_visualizations):  
            st.write(f"- {viz}")
    
    return missing_columns

# Function to load data
@st.cache_data
def load_data(uploaded_file=None, encoding="utf-8", api_data=None):
    try:
        if api_data is not None:
            df = pd.DataFrame(api_data)
            st.sidebar.success("Data successfully loaded from Flask API!")
        elif uploaded_file is not None:
            df = pd.read_csv(uploaded_file, encoding=encoding)
            st.sidebar.success(f"File successfully uploaded using {encoding} encoding!")
        else:
            # Use sample data
            data = {
                'Invoice ID': [f'INV-{i}' for i in range(1, 101)],
                'Date': pd.date_range(start='2023-01-01', periods=100).tolist(),
                'Time': [f'{h}:{m}' for h, m in zip(range(8, 20), [str(i).zfill(2) for i in range(0, 60, 36)])]*10,
                'Total': [round(100 + 900 * i/100, 2) for i in range(100)],
                'Quantity': [i % 10 + 1 for i in range(100)],
                'Unit price': [round(10 + 90 * i/100, 2) for i in range(100)],
                'Product line': ['Electronics', 'Food and beverages', 'Health and beauty', 'Sports and travel', 'Home and lifestyle'] * 20,
                'Payment': ['Cash', 'Credit card', 'Ewallet'] * 33 + ['Cash'],
                'Gender': ['Male', 'Female'] * 50,
                'Customer type': ['Member', 'Normal'] * 50
            }
            df = pd.DataFrame(data)
            st.sidebar.info("Using sample dataset. Upload your own CSV for custom analysis.")
        
        return df
    except UnicodeDecodeError as e:
        st.sidebar.warning(f"{encoding} encoding failed. Try another encoding.")
        return None
    except Exception as e:
        st.sidebar.error(f"Error reading the file: {e}")
        return None

# Handle file upload
st.sidebar.subheader("Upload Data")
selected_encoding = st.sidebar.selectbox("Select file encoding", st.session_state.encodings, index=0)
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    # Store file path in session state
    st.session_state.file_path = uploaded_file
    
    # Load data
    st.session_state.data = load_data(uploaded_file, selected_encoding)

# Check if data is loaded
if st.session_state.data is not None:
    data = st.session_state.data
    
    # Check required columns
    missing_columns = check_required_columns(data)
    
    # Data cleaning
    st.header("Data Cleaning & Exploration")
    
    try:
        st.write("Removing duplicates and handling missing values...")
        data_cleaned = data.drop_duplicates()
        data_cleaned = data_cleaned.fillna(method='ffill')
        
        if 'Date' in data_cleaned.columns:
            data_cleaned['Date'] = pd.to_datetime(data_cleaned['Date'], errors='coerce')
        
        # Display cleaned data
        st.subheader("Cleaned Data Preview")
        st.dataframe(data_cleaned.head())
        
        # Display summary statistics
        st.subheader("Statistical Summary")
        st.dataframe(data_cleaned.describe())
        
    except Exception as e:
        st.error(f"Data cleaning failed: {e}")
        data_cleaned = data.copy()
    
    # Filters
    st.sidebar.header("Filters")
    
    try:
        if 'Product line' in data_cleaned.columns:
            product_categories = ['All'] + sorted(data_cleaned['Product line'].unique().tolist())
            selected_category = st.sidebar.selectbox("Select Product Category", product_categories, key="product_category_1")
        else:
            selected_category = 'All'
            
        if 'Customer type' in data_cleaned.columns:
            customer_types = ['All'] + sorted(data_cleaned['Customer type'].unique().tolist())
            selected_customer_type = st.sidebar.selectbox("Select Customer Type", customer_types, key="customer_type_1")
        else:
            selected_customer_type = 'All'
            
        if 'Gender' in data_cleaned.columns:
            genders = ['All'] + sorted(data_cleaned['Gender'].unique().tolist())
            selected_gender = st.sidebar.selectbox("Select Gender", genders, key="gender_1")
        else:
            selected_gender = 'All'
            
        if 'Date' in data_cleaned.columns:
            try:
                min_date = data_cleaned['Date'].min().date()
                max_date = data_cleaned['Date'].max().date()
                selected_date_range = st.sidebar.date_input(
                    "Select Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="date_range_1"
                )
            except Exception as e:
                st.sidebar.warning(f"Date filter not available: {e}")
                selected_date_range = []
        else:
            selected_date_range = []
            
    except Exception as e:
        st.sidebar.error(f"Error setting up filters: {e}")
        selected_category = 'All'
        selected_customer_type = 'All'
        selected_gender = 'All'
        selected_date_range = []
    
    # Apply filters
    try:
        filtered_data = data_cleaned.copy()
        
        if 'Product line' in data_cleaned.columns and selected_category != 'All':
            filtered_data = filtered_data[filtered_data['Product line'] == selected_category]
    
        if 'Customer type' in data_cleaned.columns and selected_customer_type != 'All':
            filtered_data = filtered_data[filtered_data['Customer type'] == selected_customer_type]
    
        if 'Gender' in data_cleaned.columns and selected_gender != 'All':
            filtered_data = filtered_data[filtered_data['Gender'] == selected_gender]
    
        if 'Date' in data_cleaned.columns and len(selected_date_range) == 2:
            start_date, end_date = selected_date_range
            filtered_data = filtered_data[(filtered_data['Date'].dt.date >= start_date) & 
                                          (filtered_data['Date'].dt.date <= end_date)]
            
        # Store filtered data in session state
        st.session_state.filtered_data = filtered_data
        
        st.subheader(f"Filtered Data: {len(filtered_data)} records")
        
        # Perform customer segmentation if required columns are available
        try:
            if all(col in filtered_data.columns for col in ['Total', 'Quantity', 'Unit price']):
                data_segmented = customer_segmentation(filtered_data, n_clusters=3)
                st.write("Data cleaning and customer segmentation complete.")
            else:
                st.warning("Cannot perform customer segmentation - required columns are missing.")
                data_segmented = filtered_data.copy()  
        except Exception as e:
            st.error(f"Customer segmentation failed: {e}")
            data_segmented = filtered_data.copy()  
        
    except Exception as e:
        st.error(f"Error filtering data: {e}")
        filtered_data = data_cleaned.copy()
        st.subheader(f"Showing all data: {len(filtered_data)} records")
        data_segmented = data_cleaned.copy()
    
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Sales Distribution", 
        "Customer Demographics", 
        "Time Analysis", 
        "Advanced Analytics",
        "Forecasting"
    ])
    
    # Tab 1: Sales Distribution
    with tab1:
        st.header("Sales Distribution Analysis")
        
        # Sales by product category
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                if 'Product line' in filtered_data.columns and 'Total' in filtered_data.columns:
                    sales_by_product_category(filtered_data)
                else:
                    st.warning("Cannot display Sales by Product Category - required columns missing.")
            except Exception as e:
                st.error(f"Error displaying Sales by Product Category: {e}")
        
        with col2:
            try:
                if 'Payment' in filtered_data.columns and 'Total' in filtered_data.columns:
                    st.write("### 💳 Sales by Payment Method")
                    
                    payment_sales = filtered_data.groupby('Payment')['Total'].sum().sort_values(ascending=False).reset_index()
                    
                    fig = px.bar(
                        payment_sales,
                        x='Payment',
                        y='Total',
                        labels={'Payment': 'Payment Method', 'Total': 'Total Sales'},
                        color='Payment',
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig.update_layout(
                        xaxis_title='Payment Method',
                        yaxis_title='Total Sales',
                        plot_bgcolor='white',
                        hoverlabel=dict(bgcolor="white", font_size=12),
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Cannot display Sales by Payment Method - required columns missing.")
            except Exception as e:
                st.error(f"Error displaying Sales by Payment Method: {e}")
    
    # Tab 2: Customer Demographics
    with tab2:
        st.header("Customer Demographics Analysis")
        
        try:
            if 'Gender' in filtered_data.columns and 'Customer type' in filtered_data.columns and 'Total' in filtered_data.columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    gender_fig = plot_payment_distribution(filtered_data)
                    if gender_fig:
                        st.plotly_chart(gender_fig, use_container_width=True)
                    else:
                        st.warning("Cannot display Gender Distribution - required data missing.")
                
                with col2:
                    # Customer type pie chart
                    customer_type_sales = filtered_data.groupby('Customer type')['Total'].sum().reset_index()
                    fig_cust_type = px.pie(
                        customer_type_sales,
                        values='Total',
                        names='Customer type',
                        title='Sales by Customer Type',
                        color_discrete_sequence=px.colors.qualitative.Pastel,
                        hole=0.3
                    )
                    fig_cust_type.update_traces(textposition='inside', textinfo='percent+label')
                    fig_cust_type.update_layout(
                        legend_title_text='Customer Type',
                        margin=dict(t=50, b=0, l=0, r=0)
                    )
                    st.plotly_chart(fig_cust_type, use_container_width=True)
            else:
                st.warning("Cannot display Sales by Customer Demographics - required columns are missing.")
                
            # Customer segmentation visualization
            if 'Cluster' in data_segmented.columns:
                st.subheader("Customer Segmentation Analysis")
                
                segment_fig = plot_customer_segments(data_segmented)
                if segment_fig:
                    st.plotly_chart(segment_fig, use_container_width=True)
                
                # Segment statistics
                st.write("### Customer Segment Statistics")
                segment_stats = data_segmented.groupby('Cluster').agg({
                    'Total': ['mean', 'sum', 'count'],
                    'Quantity': ['mean', 'sum']
                }).round(2)
                
                segment_stats.columns = ['_'.join(col).strip('_') for col in segment_stats.columns.values]
                st.dataframe(segment_stats)
                
                st.write("### Segment Targeting Suggestions")
                for cluster in sorted(data_segmented['Cluster'].unique()):
                    cluster_data = data_segmented[data_segmented['Cluster'] == cluster]
                    avg_total = cluster_data['Total'].mean()
                    avg_qty = cluster_data['Quantity'].mean()
                    
                    if avg_total > data_segmented['Total'].mean() * 1.2:
                        st.info(f"💰 Segment {cluster}: High spenders (avg ${avg_total:.2f}). Target with premium products and loyalty rewards.")
                    elif avg_qty > data_segmented['Quantity'].mean() * 1.2:
                        st.info(f"🛒 Segment {cluster}: Bulk buyers (avg {avg_qty:.1f} items). Target with bundle discounts and wholesale offers.")
                    else:
                        st.info(f"👥 Segment {cluster}: Average customers (${avg_total:.2f}, {avg_qty:.1f} items). Target with general promotions.")
            
        except Exception as e:
            st.error(f"Error displaying Customer Demographics: {e}")
    
    # Tab 3: Time Analysis
    with tab3:
        st.header("Time-Based Analysis")
        
        try:
            # Daily sales trend
            if 'Date' in filtered_data.columns and 'Total' in filtered_data.columns:
                sales_by_Time(filtered_data)
            else:
                st.warning("Cannot display Time-based analysis - required columns missing.")
                
            # Hourly sales
            if 'Time' in filtered_data.columns or ('Date' in filtered_data.columns and pd.to_datetime(filtered_data['Date']).dt.time.nunique() > 1):
                st.subheader("Sales by Hour of Day")
                sales_by_hour(filtered_data)
            else:
                st.warning("Cannot display Sales by Hour - required time data is missing.")
                
            # Sales heatmap by day and hour
            st.subheader("Sales Heatmap by Day and Hour")
            plot_sales_heatmap(filtered_data)
            
        except Exception as e:
            st.error(f"Error in Time-Based Analysis: {e}")
    
    # Tab 4: Advanced Analytics
    with tab4:
        st.header("Advanced Analytics")
        
        # Correlation Analysis
        try:
            st.subheader("Correlation Analysis")
            corr_fig = plot_correlation_matrix(filtered_data)
            st.plotly_chart(corr_fig, use_container_width=True)
            
            # Product Analysis
            st.subheader("Product Category Analysis")
            product_specific_analysis(filtered_data)
            
            # Churn Prediction
            st.subheader("Customer Churn Prediction")
            st.write("""
            Churn prediction helps identify customers at risk of leaving. The model uses purchase history,
            spending habits, and time since last purchase to predict which customers might churn.
            """)
            
            # Run churn prediction
            with st.expander("Run Churn Prediction", expanded=True):
                try:
                    # Check for required columns
                    if all(col in filtered_data.columns for col in ['Date', 'Total', 'Quantity']):
                        # Prepare data for churn prediction
                        X, y = prepare_churn_data(filtered_data)
                        
                        if X is not None and y is not None:
                            st.write(f"Data prepared for churn prediction: {len(X)} records")
                            
                            # Display churn distribution
                            churn_count = pd.Series(y).value_counts().reset_index()
                            churn_count.columns = ['Churn', 'Count']
                            # Convert to string first to ensure proper mapping
                            churn_count['Churn'] = churn_count['Churn'].astype(str)
                            churn_count['Churn'] = churn_count['Churn'].replace({'0': 'Retained', '1': 'Churned'})
                            
                            # Create a pie chart for churn distribution
                            fig = px.pie(
                                churn_count, 
                                values='Count', 
                                names='Churn',
                                title='Customer Churn Distribution',
                                color_discrete_sequence=px.colors.qualitative.Set3,
                                hole=0.3
                            )
                            fig.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Train and evaluate the model
                            if st.button("Train Churn Prediction Model"):
                                with st.spinner("Training model..."):
                                    model = train_churn_model(X, y)
                                    
                                    if model is not None:
                                        # Get feature importance
                                        feature_importance = pd.DataFrame({
                                            'Feature': X.columns,
                                            'Importance': model.feature_importances_
                                        }).sort_values('Importance', ascending=False)
                                        
                                        # Display feature importance
                                        st.write("### Key Factors Influencing Churn")
                                        fig = px.bar(
                                            feature_importance,
                                            x='Importance',
                                            y='Feature',
                                            orientation='h',
                                            title='Feature Importance in Churn Prediction',
                                            color='Importance',
                                            color_continuous_scale='Viridis'
                                        )
                                        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                        # Add churn risk to the dataset
                                        filtered_data_with_risk = filtered_data.copy()
                                        proba_array = model.predict_proba(X)
                                        # Extract probability of churning (class 1)
                                        churn_probs = np.array([prob[1] for prob in proba_array])
                                        
                                        # Create risk category
                                        risk_cats = pd.cut(
                                            churn_probs, 
                                            bins=[0, 0.3, 0.7, 1], 
                                            labels=['Low Risk', 'Medium Risk', 'High Risk']
                                        )
                                        
                                        # Add predictions to data
                                        risk_df = pd.DataFrame({
                                            'Churn Probability': churn_probs,
                                            'Risk Category': risk_cats
                                        })
                                        
                                        # Display high-risk customers
                                        high_risk = risk_df[risk_df['Risk Category'] == 'High Risk']
                                        if len(high_risk) > 0:
                                            st.warning(f"⚠️ {len(high_risk)} customers ({len(high_risk)/len(risk_df)*100:.1f}%) are at high risk of churning.")
                                            
                                            # Display actionable insights
                                            st.write("### Recommended Actions for High-Risk Customers:")
                                            st.info("""
                                            1. Personalized re-engagement emails with special offers
                                            2. Loyalty program enrollment with immediate benefits
                                            3. Follow-up calls for highest-value at-risk customers
                                            4. Request feedback to identify potential issues
                                            """)
                                        else:
                                            st.success("No customers are currently at high risk of churning! 🎉")
                                
                        else:
                            st.warning("Couldn't prepare data for churn prediction. Please check your dataset.")
                    else:
                        st.warning("Missing required columns for churn prediction. Need: Date, Total, Quantity")
                except Exception as e:
                    st.error(f"Error in churn prediction: {e}")
                    import traceback
                    st.error(traceback.format_exc())
                    
            # Business Insights
            st.subheader("Business Insights & Recommendations")
            insights = generate_advanced_suggestions(filtered_data)
            
            for insight in insights:
                st.markdown(insight)
                
        except Exception as e:
            st.error(f"Error in Advanced Analytics: {e}")
    
    # Tab 5: Forecasting
    with tab5:
        st.header("Sales Forecasting")
        
        # Forecasting controls
        try:
            if 'Date' in filtered_data.columns and 'Total' in filtered_data.columns:
                forecast_periods = st.slider("Forecast Periods (Days)", min_value=7, max_value=90, value=30, step=7)
                
                col1, col2 = st.columns(2)
                with col1:
                    yearly_seasonality = st.checkbox("Yearly Seasonality", value=True)
                with col2:
                    weekly_seasonality = st.checkbox("Weekly Seasonality", value=True)
                
                if st.button("Generate Forecast"):
                    with st.spinner("Generating forecast..."):
                        # Prepare data for Prophet
                        prophet_df = prepare_sales_data_for_prophet(filtered_data, 'Date', 'Total')
                        
                        # Generate forecast
                        forecast, model = predict_sales_with_prophet(
                            prophet_df, 
                            periods=forecast_periods,
                            yearly_seasonality=yearly_seasonality,
                            weekly_seasonality=weekly_seasonality
                        )
                        
                        # Plot forecast
                        st.subheader(f"Sales Forecast for Next {forecast_periods} Days")
                        forecast_fig = plot_prophet_forecast(forecast)
                        st.plotly_chart(forecast_fig, use_container_width=True)
                        
                        # Plot components if available
                        try:
                            st.subheader("Forecast Components")
                            components = model.plot_components(forecast)
                            st.pyplot(components)
                        except Exception as e:
                            st.warning(f"Could not generate component plots: {e}")
                        
                        # Additional forecast insights
                        st.subheader("Forecast Insights")
                        
                        # Calculate forecast statistics
                        last_actual = prophet_df['y'].iloc[-1]
                        forecast_end = forecast['yhat'].iloc[-1]
                        forecast_change = ((forecast_end - last_actual) / last_actual) * 100
                        
                        # Display insights
                        if forecast_change > 10:
                            st.success(f"📈 Sales forecast shows a strong increase of {forecast_change:.1f}% over the forecast period.")
                        elif forecast_change > 0:
                            st.info(f"📈 Sales forecast shows a moderate increase of {forecast_change:.1f}% over the forecast period.")
                        elif forecast_change > -10:
                            st.warning(f"📉 Sales forecast shows a slight decrease of {abs(forecast_change):.1f}% over the forecast period.")
                        else:
                            st.error(f"📉 Sales forecast shows a significant decrease of {abs(forecast_change):.1f}% over the forecast period.")
                        
                        # Identify potential peaks and troughs
                        peak_date = forecast.loc[forecast['yhat'].idxmax(), 'ds']
                        trough_date = forecast.loc[forecast['yhat'].idxmin(), 'ds']
                        
                        st.info(f"🔼 Highest sales expected on: {peak_date.strftime('%Y-%m-%d')}")
                        st.info(f"🔽 Lowest sales expected on: {trough_date.strftime('%Y-%m-%d')}")
                        
                        # Generate actionable recommendations
                        forecast_insights = generate_advanced_suggestions(filtered_data, forecast)
                        for insight in forecast_insights[-3:]:  # Show the last 3 insights which should be forecast-related
                            st.markdown(insight)
            else:
                st.warning("Cannot perform sales forecasting - required columns 'Date' and 'Total' are missing.")
        except Exception as e:
            st.error(f"Error in Sales Forecasting: {e}")
    
    # Enable data download
    st.sidebar.header("Export Data")
    enable_data_download(filtered_data)

else:
    # Display initial instructions if no data is loaded
    st.info("👈 Please select a data source from the sidebar to get started.")
    st.write("""
    ### Getting Started
    1. Choose a data source (upload CSV, connect to API, or use sample data)
    2. Explore the dashboard tabs to analyze different aspects of your sales data
    3. Use the filters in the sidebar to focus on specific segments
    4. Download filtered data for further analysis
    
    ### Required Columns
    For full functionality, your CSV should include these columns:
    - Invoice ID: Unique identifier for each sale
    - Date: Date of the sale
    - Time: Time of the sale
    - Total: Total amount of the sale
    - Quantity: Number of items purchased
    - Unit price: Price per unit
    - Product line: Category of product
    - Payment: Payment method used
    - Gender: Customer gender
    - Customer type: Member or non-member
    """)

# Add a footer with additional information
st.sidebar.markdown("---")
st.sidebar.info(
    "This dashboard combines Flask, Streamlit, and JavaScript to analyze supermarket sales data. "
    "Use it to gain insights into sales patterns, customer behavior, and make data-driven decisions."
)
