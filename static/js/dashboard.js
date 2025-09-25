/**
 * Dashboard.js - Main JavaScript file for the Supermarket Sales Dashboard
 * Handles dashboard initialization, data loading, and UI interactions
 */

// Global variables to store data
let globalData = null;
let filteredData = null;
let currentPage = 1;
const pageSize = 10;

// Initialize the dashboard
function initializeDashboard() {
    console.log('Initializing dashboard...');
    
    // Show loading overlay
    showLoadingOverlay();
    
    // Load data from API
    loadData();
    
    // Set up event listeners
    setupEventListeners();
}

// Show loading overlay
function showLoadingOverlay() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

// Hide loading overlay
function hideLoadingOverlay() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

// Load data from API
function loadData() {
    fetch('/api/load-data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Store the data globally
                globalData = data;
                filteredData = data;
                
                // Update UI with the loaded data
                updateDashboard(data);
                
                // Populate filter dropdowns
                populateFilterDropdowns(data);
                
                // Hide loading overlay
                hideLoadingOverlay();
            } else {
                handleError(data.error || 'Failed to load data');
            }
        })
        .catch(error => {
            handleError(`Error: ${error.message}`);
        });
}

// Update dashboard with data
function updateDashboard(data) {
    // Update key stats
    updateKeyStats(data);
    
    // Update charts
    updateCharts(data);
    
    // Update data table
    updateDataTable(data);
    
    // Update top products table
    updateTopProducts(data);
}

// Update key statistics
function updateKeyStats(data) {
    if (!data || !data.sample_data) return;
    
    // Calculate stats from sample data
    let totalSales = 0;
    let totalItems = 0;
    const invoices = new Set();
    
    // Process sample data
    data.sample_data.forEach(row => {
        if (row.Total) totalSales += parseFloat(row.Total);
        if (row.Quantity) totalItems += parseInt(row.Quantity);
        if (row['Invoice ID']) invoices.add(row['Invoice ID']);
    });
    
    // Scale up based on row count ratio if we're only showing a sample
    const scaleFactor = data.row_count / data.sample_data.length;
    
    // Update UI elements
    document.getElementById('totalSales').textContent = formatCurrency(totalSales * scaleFactor);
    document.getElementById('totalTransactions').textContent = formatNumber(invoices.size * scaleFactor);
    document.getElementById('avgOrderValue').textContent = formatCurrency((totalSales / invoices.size) || 0);
    document.getElementById('totalItems').textContent = formatNumber(totalItems * scaleFactor);
}

// Update chart visualizations
function updateCharts(data) {
    if (!data || !data.sample_data || data.sample_data.length === 0) return;
    
    // Generate charts
    generateCategorySalesChart(data);
    generatePaymentMethodChart(data);
    generateSalesTrendChart(data);
    generateDemographicsCharts(data);
}

// Generate category sales chart
function generateCategorySalesChart(data) {
    if (!data.sample_data || !data.sample_data.length) return;
    
    // Check if required columns exist
    if (!data.sample_data[0].hasOwnProperty('Product line') || !data.sample_data[0].hasOwnProperty('Total')) {
        document.getElementById('categorySalesChart').innerHTML = 
            '<div class="alert alert-warning">Product line or Total columns missing from data</div>';
        return;
    }
    
    // Group by product category and sum sales
    const categorySales = {};
    data.sample_data.forEach(row => {
        const category = row['Product line'];
        const total = parseFloat(row.Total) || 0;
        
        if (category) {
            if (!categorySales[category]) {
                categorySales[category] = 0;
            }
            categorySales[category] += total;
        }
    });
    
    // Convert to arrays for plotting
    const categories = Object.keys(categorySales);
    const sales = Object.values(categorySales);
    
    // Create the chart using Plotly
    const chartData = [{
        x: categories,
        y: sales,
        type: 'bar',
        marker: {
            color: 'rgba(55, 128, 191, 0.7)',
            line: {
                color: 'rgba(55, 128, 191, 1.0)',
                width: 2
            }
        }
    }];
    
    const layout = {
        title: 'Sales by Product Category',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            color: '#fff'
        },
        xaxis: {
            title: 'Product Category',
            gridcolor: 'rgba(255,255,255,0.1)'
        },
        yaxis: {
            title: 'Total Sales',
            gridcolor: 'rgba(255,255,255,0.1)'
        }
    };
    
    Plotly.newPlot('categorySalesChart', chartData, layout);
}

// Generate payment method chart
function generatePaymentMethodChart(data) {
    if (!data.sample_data || !data.sample_data.length) return;
    
    // Check if required columns exist
    if (!data.sample_data[0].hasOwnProperty('Payment') || !data.sample_data[0].hasOwnProperty('Total')) {
        document.getElementById('paymentMethodChart').innerHTML = 
            '<div class="alert alert-warning">Payment or Total columns missing from data</div>';
        return;
    }
    
    // Group by payment method and sum sales
    const paymentSales = {};
    data.sample_data.forEach(row => {
        const payment = row.Payment;
        const total = parseFloat(row.Total) || 0;
        
        if (payment) {
            if (!paymentSales[payment]) {
                paymentSales[payment] = 0;
            }
            paymentSales[payment] += total;
        }
    });
    
    // Convert to arrays for plotting
    const methods = Object.keys(paymentSales);
    const sales = Object.values(paymentSales);
    
    // Create the chart using Plotly
    const chartData = [{
        labels: methods,
        values: sales,
        type: 'pie',
        hole: 0.4,
        marker: {
            colors: ['#3366CC', '#DC3912', '#FF9900', '#109618']
        },
        textinfo: 'label+percent',
        textposition: 'outside'
    }];
    
    const layout = {
        title: 'Sales by Payment Method',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            color: '#fff'
        },
        showlegend: false
    };
    
    Plotly.newPlot('paymentMethodChart', chartData, layout);
}

// Generate sales trend chart
function generateSalesTrendChart(data) {
    if (!data.sample_data || !data.sample_data.length) return;
    
    // Check if required columns exist
    if (!data.sample_data[0].hasOwnProperty('Date') || !data.sample_data[0].hasOwnProperty('Total')) {
        document.getElementById('salesTrendChart').innerHTML = 
            '<div class="alert alert-warning">Date or Total columns missing from data</div>';
        return;
    }
    
    // Group by date and sum sales
    const salesByDate = {};
    data.sample_data.forEach(row => {
        // Convert date string to Date object
        const dateStr = row.Date;
        if (!dateStr) return;
        
        // Parse the date (handle different formats)
        let date;
        if (dateStr.includes('-')) {
            // ISO format: 2023-01-15
            date = dateStr.split('T')[0]; // Handle if datetime
        } else if (dateStr.includes('/')) {
            // US format: MM/DD/YYYY
            const parts = dateStr.split('/');
            date = `${parts[2]}-${parts[0].padStart(2, '0')}-${parts[1].padStart(2, '0')}`;
        } else {
            // Unknown format
            return;
        }
        
        const total = parseFloat(row.Total) || 0;
        
        if (!salesByDate[date]) {
            salesByDate[date] = 0;
        }
        salesByDate[date] += total;
    });
    
    // Convert to arrays and sort by date
    const dates = Object.keys(salesByDate).sort();
    const sales = dates.map(date => salesByDate[date]);
    
    // Create the chart using Plotly
    const chartData = [{
        x: dates,
        y: sales,
        type: 'scatter',
        mode: 'lines+markers',
        line: {
            color: '#00bfff',
            width: 2
        },
        marker: {
            color: '#ffffff',
            size: 6
        }
    }];
    
    const layout = {
        title: 'Daily Sales Trend',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            color: '#fff'
        },
        xaxis: {
            title: 'Date',
            gridcolor: 'rgba(255,255,255,0.1)'
        },
        yaxis: {
            title: 'Total Sales',
            gridcolor: 'rgba(255,255,255,0.1)'
        }
    };
    
    Plotly.newPlot('salesTrendChart', chartData, layout);
}

// Generate demographics charts
function generateDemographicsCharts(data) {
    if (!data.sample_data || !data.sample_data.length) return;
    
    // Gender distribution chart
    if (data.sample_data[0].hasOwnProperty('Gender') && data.sample_data[0].hasOwnProperty('Total')) {
        // Group by gender and sum sales
        const genderSales = {};
        data.sample_data.forEach(row => {
            const gender = row.Gender;
            const total = parseFloat(row.Total) || 0;
            
            if (gender) {
                if (!genderSales[gender]) {
                    genderSales[gender] = 0;
                }
                genderSales[gender] += total;
            }
        });
        
        // Convert to arrays for plotting
        const genders = Object.keys(genderSales);
        const sales = Object.values(genderSales);
        
        // Create the chart using Plotly
        const chartData = [{
            labels: genders,
            values: sales,
            type: 'pie',
            hole: 0.4,
            marker: {
                colors: ['#5D69B1', '#E58606']
            },
            textinfo: 'label+percent',
            textposition: 'inside'
        }];
        
        const layout = {
            title: 'Sales by Gender',
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {
                color: '#fff'
            },
            showlegend: false
        };
        
        Plotly.newPlot('genderDistributionChart', chartData, layout);
    } else {
        document.getElementById('genderDistributionChart').innerHTML = 
            '<div class="alert alert-warning">Gender or Total columns missing</div>';
    }
    
    // Customer type chart
    if (data.sample_data[0].hasOwnProperty('Customer type') && data.sample_data[0].hasOwnProperty('Total')) {
        // Group by customer type and sum sales
        const customerSales = {};
        data.sample_data.forEach(row => {
            const type = row['Customer type'];
            const total = parseFloat(row.Total) || 0;
            
            if (type) {
                if (!customerSales[type]) {
                    customerSales[type] = 0;
                }
                customerSales[type] += total;
            }
        });
        
        // Convert to arrays for plotting
        const types = Object.keys(customerSales);
        const sales = Object.values(customerSales);
        
        // Create the chart using Plotly
        const chartData = [{
            labels: types,
            values: sales,
            type: 'pie',
            hole: 0.4,
            marker: {
                colors: ['#52BCA3', '#99C945']
            },
            textinfo: 'label+percent',
            textposition: 'inside'
        }];
        
        const layout = {
            title: 'Sales by Customer Type',
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {
                color: '#fff'
            },
            showlegend: false
        };
        
        Plotly.newPlot('customerTypeChart', chartData, layout);
    } else {
        document.getElementById('customerTypeChart').innerHTML = 
            '<div class="alert alert-warning">Customer type or Total columns missing</div>';
    }
}

// Update data table
function updateDataTable(data) {
    if (!data || !data.sample_data || data.sample_data.length === 0) return;
    
    const tableHead = document.querySelector('#dataTable thead tr');
    const tableBody = document.querySelector('#dataTable tbody');
    
    // Clear existing content
    tableHead.innerHTML = '';
    tableBody.innerHTML = '';
    
    // Add table headers
    const columns = data.columns || Object.keys(data.sample_data[0]);
    columns.forEach(column => {
        const th = document.createElement('th');
        th.textContent = column;
        tableHead.appendChild(th);
    });
    
    // Add table rows (paginated)
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, data.sample_data.length);
    
    for (let i = startIndex; i < endIndex; i++) {
        const row = data.sample_data[i];
        const tr = document.createElement('tr');
        
        columns.forEach(column => {
            const td = document.createElement('td');
            td.textContent = row[column] || '';
            tr.appendChild(td);
        });
        
        tableBody.appendChild(tr);
    }
    
    // Update pagination
    updatePagination(data.sample_data.length);
}

// Update pagination controls
function updatePagination(totalRows) {
    const totalPages = Math.ceil(totalRows / pageSize);
    
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');
    const dataStats = document.getElementById('dataStats');
    
    // Update page info
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    
    // Update data stats
    const startIndex = (currentPage - 1) * pageSize + 1;
    const endIndex = Math.min(currentPage * pageSize, totalRows);
    dataStats.textContent = `Showing ${startIndex} to ${endIndex} of ${totalRows} records`;
    
    // Enable/disable buttons
    prevButton.disabled = currentPage <= 1;
    nextButton.disabled = currentPage >= totalPages;
    
    // Add click handlers
    prevButton.onclick = () => {
        if (currentPage > 1) {
            currentPage--;
            updateDataTable(filteredData);
        }
    };
    
    nextButton.onclick = () => {
        if (currentPage < totalPages) {
            currentPage++;
            updateDataTable(filteredData);
        }
    };
}

// Update top products table
function updateTopProducts(data) {
    if (!data || !data.sample_data || data.sample_data.length === 0) return;
    
    // Check if required columns exist
    if (!data.sample_data[0].hasOwnProperty('Product line') || 
        !data.sample_data[0].hasOwnProperty('Total') || 
        !data.sample_data[0].hasOwnProperty('Quantity')) {
        document.getElementById('topProductsTable').innerHTML = 
            '<div class="alert alert-warning">Required columns missing for top products</div>';
        return;
    }
    
    // Group by product category
    const productStats = {};
    let totalSales = 0;
    
    data.sample_data.forEach(row => {
        const category = row['Product line'];
        const total = parseFloat(row.Total) || 0;
        const quantity = parseInt(row.Quantity) || 0;
        
        totalSales += total;
        
        if (category) {
            if (!productStats[category]) {
                productStats[category] = { sales: 0, quantity: 0 };
            }
            productStats[category].sales += total;
            productStats[category].quantity += quantity;
        }
    });
    
    // Convert to array and sort by sales
    const products = Object.keys(productStats).map(category => ({
        category,
        sales: productStats[category].sales,
        quantity: productStats[category].quantity,
        percentage: (productStats[category].sales / totalSales) * 100
    }));
    
    products.sort((a, b) => b.sales - a.sales);
    
    // Update table
    const tableBody = document.querySelector('#topProductsTable tbody');
    tableBody.innerHTML = '';
    
    // Show top 5 products
    const topProducts = products.slice(0, 5);
    
    topProducts.forEach(product => {
        const tr = document.createElement('tr');
        
        const tdCategory = document.createElement('td');
        tdCategory.textContent = product.category;
        
        const tdSales = document.createElement('td');
        tdSales.textContent = formatCurrency(product.sales);
        
        const tdQuantity = document.createElement('td');
        tdQuantity.textContent = product.quantity;
        
        const tdPercentage = document.createElement('td');
        tdPercentage.textContent = `${product.percentage.toFixed(2)}%`;
        
        tr.appendChild(tdCategory);
        tr.appendChild(tdSales);
        tr.appendChild(tdQuantity);
        tr.appendChild(tdPercentage);
        
        tableBody.appendChild(tr);
    });
}

// Populate filter dropdowns
function populateFilterDropdowns(data) {
    if (!data || !data.sample_data || data.sample_data.length === 0) return;
    
    // Category filter
    if (data.sample_data[0].hasOwnProperty('Product line')) {
        const categories = new Set();
        data.sample_data.forEach(row => {
            if (row['Product line']) categories.add(row['Product line']);
        });
        
        const categoryFilter = document.getElementById('categoryFilter');
        categoryFilter.innerHTML = '<option value="All" selected>All Categories</option>';
        
        Array.from(categories).sort().forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categoryFilter.appendChild(option);
        });
    }
    
    // Customer type filter
    if (data.sample_data[0].hasOwnProperty('Customer type')) {
        const types = new Set();
        data.sample_data.forEach(row => {
            if (row['Customer type']) types.add(row['Customer type']);
        });
        
        const typeFilter = document.getElementById('customerTypeFilter');
        typeFilter.innerHTML = '<option value="All" selected>All Types</option>';
        
        Array.from(types).sort().forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            typeFilter.appendChild(option);
        });
    }
    
    // Gender filter
    if (data.sample_data[0].hasOwnProperty('Gender')) {
        const genders = new Set();
        data.sample_data.forEach(row => {
            if (row.Gender) genders.add(row.Gender);
        });
        
        const genderFilter = document.getElementById('genderFilter');
        genderFilter.innerHTML = '<option value="All" selected>All Genders</option>';
        
        Array.from(genders).sort().forEach(gender => {
            const option = document.createElement('option');
            option.value = gender;
            option.textContent = gender;
            genderFilter.appendChild(option);
        });
    }
    
    // Date range filters
    if (data.sample_data[0].hasOwnProperty('Date')) {
        // Find min and max dates
        let minDate = null;
        let maxDate = null;
        
        data.sample_data.forEach(row => {
            if (!row.Date) return;
            
            const date = new Date(row.Date);
            if (isNaN(date.getTime())) return;
            
            if (!minDate || date < minDate) minDate = date;
            if (!maxDate || date > maxDate) maxDate = date;
        });
        
        if (minDate && maxDate) {
            const startDateInput = document.getElementById('startDate');
            const endDateInput = document.getElementById('endDate');
            
            // Format dates for input elements
            const formatDate = date => {
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                return `${year}-${month}-${day}`;
            };
            
            startDateInput.value = formatDate(minDate);
            startDateInput.min = formatDate(minDate);
            startDateInput.max = formatDate(maxDate);
            
            endDateInput.value = formatDate(maxDate);
            endDateInput.min = formatDate(minDate);
            endDateInput.max = formatDate(maxDate);
        }
    }
}

// Set up event listeners
function setupEventListeners() {
    // Filter form submission
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyFilters();
        });
    }
    
    // Reset filters button
    const resetFiltersBtn = document.getElementById('resetFiltersBtn');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            resetFilters();
        });
    }
    
    // Refresh data button
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            loadData();
        });
    }
    
    // Export data button
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            exportDataToCSV();
        });
    }
}

// Apply filters to the data
function applyFilters() {
    showLoadingOverlay();
    
    // Get filter values
    const category = document.getElementById('categoryFilter').value;
    const customerType = document.getElementById('customerTypeFilter').value;
    const gender = document.getElementById('genderFilter').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const encoding = document.getElementById('encodingFilter').value;
    
    // Build filters object
    const filters = {
        category: category,
        customer_type: customerType,
        gender: gender,
        date_range: []
    };
    
    if (startDate && endDate) {
        filters.date_range = [startDate, endDate];
    }
    
    // Reset current page
    currentPage = 1;
    
    // Call API with filters
    fetch('/api/filter-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filters: filters,
            encoding: encoding
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update filtered data
            filteredData = {
                ...globalData,
                sample_data: data.filtered_sample,
                row_count: data.filtered_row_count
            };
            
            // Update UI with filtered data
            updateDashboard(filteredData);
            hideLoadingOverlay();
        } else {
            handleError(data.error || 'Failed to apply filters');
        }
    })
    .catch(error => {
        handleError(`Error applying filters: ${error.message}`);
    });
}

// Reset filters to default values
function resetFilters() {
    // Reset form values
    document.getElementById('filterForm').reset();
    
    // Reset date inputs if present
    if (globalData && globalData.sample_data && globalData.sample_data.length > 0) {
        populateFilterDropdowns(globalData);
    }
    
    // Reset to original data
    filteredData = globalData;
    currentPage = 1;
    
    // Update UI
    if (filteredData) {
        updateDashboard(filteredData);
    }
}

// Export filtered data to CSV
function exportDataToCSV() {
    if (!filteredData || !filteredData.sample_data || filteredData.sample_data.length === 0) {
        alert('No data to export');
        return;
    }
    
    // Get headers
    const headers = filteredData.columns || Object.keys(filteredData.sample_data[0]);
    
    // Convert data to CSV
    let csvContent = headers.join(',') + '\n';
    
    filteredData.sample_data.forEach(row => {
        const values = headers.map(header => {
            const value = row[header] || '';
            // Escape values with commas
            return typeof value === 'string' && value.includes(',') 
                ? `"${value}"` 
                : value;
        });
        csvContent += values.join(',') + '\n';
    });
    
    // Create and download CSV file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    
    link.setAttribute('href', url);
    link.setAttribute('download', 'supermarket_sales_data.csv');
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Handle errors
function handleError(message) {
    console.error(message);
    hideLoadingOverlay();
    
    // Display error message to user
    alert(`Error: ${message}`);
}

// Format currency values
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

// Format number values
function formatNumber(value) {
    return new Intl.NumberFormat('en-US').format(value);
}

