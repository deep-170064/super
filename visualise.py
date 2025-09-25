import plotly.express as px
import streamlit as st
import pandas as pd
import seaborn as sns
import plotly.graph_objects as go

def plot_sales_heatmap(filtered_data):
    try:
        if filtered_data.empty:
            st.warning("No data available to plot the heatmap.")
            return
        required_columns = ['Date', 'Time', 'Total']
        if not all(col in filtered_data.columns for col in required_columns):
            st.warning(f"Missing one or more required columns: {', '.join(required_columns)}")
            return
        filtered_data['Date'] = pd.to_datetime(filtered_data['Date'], errors='coerce')
        filtered_data['Day'] = pd.Categorical(
            filtered_data['Date'].dt.day_name(),
            categories=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            ordered=True
        )
        if 'Hour' not in filtered_data.columns:
            filtered_data['Hour'] = pd.to_numeric(filtered_data['Time'].str.split(':').str[0], errors='coerce')
        heatmap_data = filtered_data.groupby(['Day', 'Hour'])['Total'].sum().reset_index()
        fig = px.density_heatmap(
            heatmap_data, x='Hour', y='Day', z='Total',
            color_continuous_scale='Plasma',  
            category_orders={"Day": ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']},
            title="Sales Heatmap by Day and Hour"
        )

        fig.update_layout(
            xaxis_title="Hour of the Day",
            yaxis_title="Day of the Week",
            font=dict(family="Arial", size=12),
            coloraxis_colorbar=dict(title="Total Sales"),
            template="plotly_white"
        )

        st.plotly_chart(fig)

    except Exception as e:
        st.error(f"Error while generating heatmap: {e}")

def sales_by_product_category(filtered_data):
    if 'Product line' in filtered_data.columns and 'Total' in filtered_data.columns:
        st.write("### Sales by Product Category")

        category_sales = filtered_data.groupby('Product line')['Total'].sum().reset_index()

        fig = px.bar(category_sales, 
                     x='Product line', 
                     y='Total', 
                     color='Total',
                     text='Total',
                     color_continuous_scale='viridis')

        fig.update_layout(
            xaxis_title="Product Category",
            yaxis_title="Total Sales",
            title="Total Sales by Product Category",
            xaxis_tickangle=-45
        )

        st.plotly_chart(fig)

def sales_by_Time(filtered_data):
    if 'Date' in filtered_data.columns and 'Total' in filtered_data.columns:
        st.write("### Sales Trends Over Time")
        filtered_data['Date'] = pd.to_datetime(filtered_data['Date'])
        daily_sales = filtered_data.groupby(filtered_data['Date'].dt.date)['Total'].sum().reset_index()
        daily_sales.columns = ['Date', 'Total Sales']
        fig = px.line(daily_sales, x='Date', y='Total Sales', 
                      markers=True, title='Daily Sales Trend')
        fig.update_layout(xaxis_title='Date', yaxis_title='Total Sales', 
                          xaxis_tickangle=-45, template='plotly_dark')
        
        st.plotly_chart(fig)

def sales_by_hour(data):
    """Plots total sales distribution by hour of the day."""
    
    if 'Time' not in data.columns or 'Total' not in data.columns:
        st.warning("Time or Total column not found in dataset.")
        return
    if data['Time'].dtype == 'object':
        try:
            data['Hour'] = pd.to_datetime(data['Time']).dt.hour
        except:
            data['Hour'] = data['Time'].str.split(':', expand=True)[0].astype(int)
    hourly_sales = data.groupby('Hour')['Total'].sum().reset_index()
    fig = px.bar(
        hourly_sales, 
        x='Hour', 
        y='Total', 
        text_auto=True,
        color='Total',
        color_continuous_scale='Viridis',
        labels={'Hour': 'Hour of Day', 'Total': 'Total Sales'},
        title='Sales by Hour of Day'
    )
    fig.update_traces(marker_line_width=1.5, marker_line_color='black')
    fig.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
    st.plotly_chart(fig)

def product_specific_analysis(filtered_data):
    if 'Product line' in filtered_data.columns and 'Unit price' in filtered_data.columns and 'Quantity' in filtered_data.columns:
        st.subheader("Product Analysis")
        avg_price = filtered_data.groupby('Product line')['Unit price'].mean().reset_index()

        fig1 = px.bar(avg_price, 
                      x='Product line', 
                      y='Unit price', 
                      color='Unit price',
                      text='Unit price',
                      title="Average Unit Price by Product Category",
                      color_continuous_scale='viridis')

        fig1.update_layout(xaxis_tickangle=-45, xaxis_title="Product Category", yaxis_title="Average Unit Price")
        st.plotly_chart(fig1)
        qty_sold = filtered_data.groupby('Product line')['Quantity'].sum().reset_index()

        fig2 = px.bar(qty_sold, 
                      x='Product line', 
                      y='Quantity', 
                      color='Quantity',
                      text='Quantity',
                      title="Quantity Sold by Product Category",
                      color_continuous_scale='blues')

        fig2.update_layout(xaxis_tickangle=-45, xaxis_title="Product Category", yaxis_title="Total Quantity Sold")
        st.plotly_chart(fig2)

def plot_category_sales(filtered_data):
    try:
        if filtered_data.empty:
            st.warning("No data available to plot product category sales.")
            return
        if not all(col in filtered_data.columns for col in ['Product line', 'Total']):
            st.warning("Required columns missing for product category visualization.")
            return
        st.write("### Interactive Sales by Product Category")
        category_sales = filtered_data.groupby('Product line')['Total'].sum().sort_values(ascending=False)
        fig = px.bar(
            x=category_sales.index,
            y=category_sales.values,
            labels={'x': 'Product Category', 'y': 'Total Sales'},
            color=category_sales.index,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_layout(title='Total Sales by Product Category')
        st.plotly_chart(fig)

    except Exception as e:
        st.error(f"Error while generating product category plot: {e}")

def enable_data_download(filtered_data):
    try:
        if filtered_data.empty:
            st.warning("No data available for download.")
            return
        
        csv_data = filtered_data.to_csv(index=False).encode('utf-8')
        st.download_button(label='Download as CSV', data=csv_data, file_name='filtered_data.csv', mime='text/csv')

    except Exception as e:
        st.error(f"Error during CSV export: {e}")

def plot_prophet_forecast(forecast, title="Sales Forecast with Prophet"):
    """
    Plot the Prophet forecast results.
    
    Parameters:
    -----------
    forecast : pandas.DataFrame
        DataFrame returned from Prophet's predict() method (merged with actual values if available),
        containing at least the columns:
            - 'ds' (dates)
            - 'yhat' (predicted values)
            - 'yhat_lower' (lower prediction bound)
            - 'yhat_upper' (upper prediction bound)
            - optionally, 'y' (actual values)
    title : str, default="Sales Forecast with Prophet"
        Title for the plot.
        
    Returns:
    --------
    fig : plotly.graph_objs._figure.Figure
        A Plotly Figure object.
    """
    fig = px.line(
        forecast, 
        x='ds', 
        y='yhat', 
        title=title, 
        labels={'ds': 'Date', 'yhat': 'Predicted Sales'}
    )
    if 'y' in forecast.columns:
        fig.add_scatter(
            x=forecast['ds'], 
            y=forecast['y'], 
            mode='markers', 
            name='Actual Sales',
            marker=dict(color='black', size=5)
        )
    fig.add_scatter(
        x=forecast['ds'],
        y=forecast['yhat_lower'],
        mode='lines',
        name='Lower Bound',
        line=dict(dash='dash', color='gray')
    )
    
    fig.add_scatter(
        x=forecast['ds'],
        y=forecast['yhat_upper'],
        mode='lines',
        name='Upper Bound',
        line=dict(dash='dash', color='gray')
    )
    
    return fig

def plot_correlation_matrix(df):
    """
    Plot a correlation matrix of numeric columns in the DataFrame.
    """
    numeric_cols = df.select_dtypes(include=['number']).columns
    corr_matrix = df[numeric_cols].corr()
    
    # Create correlation heatmap
    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        color_continuous_scale='RdBu_r',
        title="Correlation Matrix"
    )
    
    fig.update_layout(
         width=900,
        height=800,
        xaxis_title="",
        yaxis_title="",
        xaxis=dict(tickangle=-45),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def plot_customer_segments(df):
    """
    Plot visualization of customer segments based on Total and Quantity.
    """
    if 'Cluster' not in df.columns:
        return None
    
    # Create a scatter plot of Total vs Quantity colored by Cluster
    fig = px.scatter(
        df, 
        x='Total', 
        y='Quantity',
        color='Cluster',
        hover_data=['Invoice ID', 'Total', 'Quantity'],
        title="Customer Segments",
        labels={'Total': 'Total Purchase Amount', 'Quantity': 'Items Purchased'}
    )
    
    fig.update_layout(
        legend_title="Customer Segment",
        xaxis_title="Total Purchase Amount",
        yaxis_title="Number of Items Purchased",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def plot_payment_distribution(df):
    """
    Plot payment method distribution.
    """
    if 'Payment' not in df.columns:
        return None
    
    payment_counts = df['Payment'].value_counts().reset_index()
    payment_counts.columns = ['Payment Method', 'Count']
    
    fig = px.pie(
        payment_counts,
        values='Count',
        names='Payment Method',
        title='Payment Method Distribution',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hole=0.4
    )
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig
