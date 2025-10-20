/**
 * Charts.js - JavaScript file for chart handling in the Supermarket Sales Dashboard
 * Handles advanced chart generation for Analysis and Forecast pages
 */

// Initialize the analysis page
function initializeAnalysis() {
    console.log('Initializing analysis page...');
    
    // Load data for initial setup
    loadAnalysisData();
    
    // Set up event listeners
    setupAnalysisEventListeners();
}

// Initialize the forecast page
function initializeForecast() {
    console.log('Initializing forecast page...');
    
    // Load data for forecast setup
    loadForecastData();
    
    // Set up event listeners
    setupForecastEventListeners();
}

// Load data for analysis
function loadAnalysisData() {
    fetch('/api/load-data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Populate filter dropdowns
                populateAnalysisFilterDropdowns(data);
                
                // Load initial tab
                loadAnalysisTab('segmentation');
            } else {
                handleAnalysisError(data.error || 'Failed to load data');
            }
        })
        .catch(error => {
            handleAnalysisError(`Error: ${error.message}`);
        });
}

// Load data for forecast
function loadForecastData() {
    fetch('/api/load-data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Populate filter dropdowns
                populateForecastFilterDropdowns(data);
            } else {
                handleForecastError(data.error || 'Failed to load data');
            }
        })
        .catch(error => {
            handleForecastError(`Error: ${error.message}`);
        });
}

// Set up event listeners for analysis page
function setupAnalysisEventListeners() {
    // Analysis filter form submission
    const analysisFilterForm = document.getElementById('analysisFilterForm');
    if (analysisFilterForm) {
        analysisFilterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const analysisType = document.getElementById('analysisType').value;
            loadAnalysisTab(analysisType);
        });
    }
    
    // Reset analysis filters button
    const resetAnalysisFiltersBtn = document.getElementById('resetAnalysisFiltersBtn');
    if (resetAnalysisFiltersBtn) {
        resetAnalysisFiltersBtn.addEventListener('click', function() {
            resetAnalysisFilters();
        });
    }
    
    // Run segmentation button
    const runSegmentationBtn = document.getElementById('runSegmentationBtn');
    if (runSegmentationBtn) {
        runSegmentationBtn.addEventListener('click', function() {
            runCustomerSegmentation();
        });
    }
    
    // Run churn prediction button
    const runChurnPredictionBtn = document.getElementById('runChurnPredictionBtn');
    if (runChurnPredictionBtn) {
        runChurnPredictionBtn.addEventListener('click', function() {
            performChurnPrediction();
        });
    }
    
    // Generate insights button
    const generateInsightsBtn = document.getElementById('generateInsightsBtn');
    if (generateInsightsBtn) {
        generateInsightsBtn.addEventListener('click', function() {
            generateBusinessInsights();
        });
    }
}

// Set up event listeners for forecast page
function setupForecastEventListeners() {
    // Forecast form submission
    const forecastForm = document.getElementById('forecastForm');
    if (forecastForm) {
        forecastForm.addEventListener('submit', function(e) {
            e.preventDefault();
            generateSalesForecast();
        });
    }
    
    // Forecast filter form submission
    const forecastFilterForm = document.getElementById('forecastFilterForm');
    if (forecastFilterForm) {
        forecastFilterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // This will re-run the forecast with current filters
            generateSalesForecast();
        });
    }
    
    // Download forecast button
    const downloadForecastBtn = document.getElementById('downloadForecastBtn');
    if (downloadForecastBtn) {
        downloadForecastBtn.addEventListener('click', function() {
            downloadForecastData();
        });
    }
}

// Populate filter dropdowns for analysis page
function populateAnalysisFilterDropdowns(data) {
    if (!data || !data.sample_data || data.sample_data.length === 0) return;
    
    // Category filter
    if (data.sample_data[0].hasOwnProperty('Product line')) {
        const categories = new Set();
        data.sample_data.forEach(row => {
            if (row['Product line']) categories.add(row['Product line']);
        });
        
        const categoryFilter = document.getElementById('categoryFilterAnalysis');
        if (categoryFilter) {
            categoryFilter.innerHTML = '<option value="All" selected>All Categories</option>';
            
            Array.from(categories).sort().forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                categoryFilter.appendChild(option);
            });
        }
    }
    
    // Customer type filter
    if (data.sample_data[0].hasOwnProperty('Customer type')) {
        const types = new Set();
        data.sample_data.forEach(row => {
            if (row['Customer type']) types.add(row['Customer type']);
        });
        
        const typeFilter = document.getElementById('customerTypeFilterAnalysis');
        if (typeFilter) {
            typeFilter.innerHTML = '<option value="All" selected>All Types</option>';
            
            Array.from(types).sort().forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                typeFilter.appendChild(option);
            });
        }
    }
    
    // Gender filter
    if (data.sample_data[0].hasOwnProperty('Gender')) {
        const genders = new Set();
        data.sample_data.forEach(row => {
            if (row.Gender) genders.add(row.Gender);
        });
        
        const genderFilter = document.getElementById('genderFilterAnalysis');
        if (genderFilter) {
            genderFilter.innerHTML = '<option value="All" selected>All Genders</option>';
            
            Array.from(genders).sort().forEach(gender => {
                const option = document.createElement('option');
                option.value = gender;
                option.textContent = gender;
                genderFilter.appendChild(option);
            });
        }
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
            const startDateInput = document.getElementById('startDateAnalysis');
            const endDateInput = document.getElementById('endDateAnalysis');
            
            if (startDateInput && endDateInput) {
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
}

// Populate filter dropdowns for forecast page
function populateForecastFilterDropdowns(data) {
    if (!data || !data.sample_data || data.sample_data.length === 0) return;
    
    // Category filter
    if (data.sample_data[0].hasOwnProperty('Product line')) {
        const categories = new Set();
        data.sample_data.forEach(row => {
            if (row['Product line']) categories.add(row['Product line']);
        });
        
        const categoryFilter = document.getElementById('categoryFilterForecast');
        if (categoryFilter) {
            categoryFilter.innerHTML = '<option value="All" selected>All Categories</option>';
            
            Array.from(categories).sort().forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                categoryFilter.appendChild(option);
            });
        }
    }
    
    // Customer type filter
    if (data.sample_data[0].hasOwnProperty('Customer type')) {
        const types = new Set();
        data.sample_data.forEach(row => {
            if (row['Customer type']) types.add(row['Customer type']);
        });
        
        const typeFilter = document.getElementById('customerTypeFilterForecast');
        if (typeFilter) {
            typeFilter.innerHTML = '<option value="All" selected>All Types</option>';
            
            Array.from(types).sort().forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                typeFilter.appendChild(option);
            });
        }
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
            const startDateInput = document.getElementById('startDateForecast');
            const endDateInput = document.getElementById('endDateForecast');
            
            if (startDateInput && endDateInput) {
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
}

// Reset analysis filters
function resetAnalysisFilters() {
    // Reset form values
    const analysisFilterForm = document.getElementById('analysisFilterForm');
    if (analysisFilterForm) {
        analysisFilterForm.reset();
    }
    
    // Re-load data for analysis
    loadAnalysisData();
}

// Load specific analysis tab content
function loadAnalysisTab(tabId) {
    console.log(`Loading analysis tab: ${tabId}`);
    
    // Show loading overlay
    document.getElementById('analysisLoadingOverlay').style.display = 'flex';
    
    switch(tabId) {
        case 'segmentation':
            fetchCustomerSegmentation();
            break;
        case 'correlation':
            fetchCorrelationAnalysis();
            break;
        case 'product':
            fetchProductAnalysis();
            break;
        case 'time':
            fetchTimeAnalysis();
            break;
        case 'churn':
            setupChurnPrediction();
            break;
        case 'insights':
            fetchInsights();
            break;
        default:
            document.getElementById('analysisLoadingOverlay').style.display = 'none';
            console.log(`Unknown tab ID: ${tabId}`);
    }
}

// Fetch and display customer segmentation
function fetchCustomerSegmentation() {
    // Get the cluster count
    const clusterCount = document.getElementById('clusterCount').value;
    
    // Get current filter values
    const filters = getAnalysisFilterValues();
    
    // Call API to perform segmentation
    fetch('/api/customer-segmentation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            n_clusters: parseInt(clusterCount),
            encoding: 'utf-8',
            ...filters
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displaySegmentationResults(data);
        } else {
            handleAnalysisError(data.error || 'Failed to perform customer segmentation');
        }
        document.getElementById('analysisLoadingOverlay').style.display = 'none';
    })
    .catch(error => {
        handleAnalysisError(`Error in customer segmentation: ${error.message}`);
        document.getElementById('analysisLoadingOverlay').style.display = 'none';
    });
}

// Display segmentation results - Updated for Cluster_ field
function displaySegmentationResults(data) {
    // Create scatter plot visualization of clusters
    const clusters = data.clusters;
    
    // Create a colored scatter plot
    const traces = [];
    
    // Create dummy data for visualization since we don't have actual coordinates
    // In a real scenario, you'd use the actual features used for clustering
    for (let i = 0; i < data.n_clusters; i++) {
        const cluster = clusters.find(c => c.Cluster_ === i) || { 
            Cluster_: i, 
            Total_mean: Math.random() * 100, 
            Quantity_mean: Math.random() * 10,
            Total_count: Math.round(Math.random() * 100)
        };
        
        traces.push({
            x: [cluster.Total_mean],
            y: [cluster.Quantity_mean],
            mode: 'markers',
            name: `Cluster ${i}`,
            text: [`Cluster ${i} (${cluster.Total_count || 0} customers)`],
            marker: {
                size: Math.max(10, Math.min(50, (cluster.Total_count || 20) / 2)),
                color: getClusterColor(i),
                line: {
                    color: 'white',
                    width: 2
                }
            }
        });
    }
    
    const layout = {
        title: `Customer Segmentation (${data.n_clusters} clusters)`,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            color: '#fff'
        },
        xaxis: {
            title: 'Average Purchase Value',
            gridcolor: 'rgba(255,255,255,0.1)'
        },
        yaxis: {
            title: 'Average Quantity',
            gridcolor: 'rgba(255,255,255,0.1)'
        },
        showlegend: true,
        legend: {
            x: 0,
            y: 1
        }
    };
    
    Plotly.newPlot('segmentationChart', traces, layout);
    
    // Display segment profiles
    const segmentProfiles = document.getElementById('segmentProfiles');
    if (!segmentProfiles) {
        console.error('segmentProfiles element not found!');
        return;
    }
    
    segmentProfiles.innerHTML = '';
    
    // Check if clusters exist and have data
    if (!clusters || clusters.length === 0) {
        segmentProfiles.innerHTML = '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle me-2"></i>No cluster data available</div>';
        console.warn('No clusters data found');
        return;
    }
    
    clusters.forEach(cluster => {
        const card = document.createElement('div');
        card.className = 'card bg-dark mb-3';
        
        const cardHeader = document.createElement('div');
        cardHeader.className = 'card-header d-flex justify-content-between align-items-center';
        cardHeader.innerHTML = `
            <h6 class="mb-0">Cluster ${cluster.Cluster_}</h6>
            <span class="badge bg-primary">${cluster.Total_count || 0} customers</span>
        `;
        
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        
        const avgTotal = cluster.Total_mean ? parseFloat(cluster.Total_mean).toFixed(2) : 'N/A';
        const avgQuantity = cluster.Quantity_mean ? parseFloat(cluster.Quantity_mean).toFixed(2) : 'N/A';
        const totalSales = cluster.Total_sum ? parseFloat(cluster.Total_sum).toFixed(2) : 'N/A';
        
        cardBody.innerHTML = `
            <p class="mb-1"><strong>Avg. Purchase:</strong> $${avgTotal}</p>
            <p class="mb-1"><strong>Avg. Quantity:</strong> ${avgQuantity} items</p>
            <p class="mb-1"><strong>Total Sales:</strong> $${totalSales}</p>
            <p class="mb-0 text-${getSegmentActionColor(cluster.Cluster_)}">
                ${getSegmentActionText(cluster.Cluster_, parseFloat(avgTotal), parseFloat(avgQuantity))}
            </p>
        `;
        
        card.appendChild(cardHeader);
        card.appendChild(cardBody);
        segmentProfiles.appendChild(card);
    });
}

// Get color for cluster visualization
function getClusterColor(clusterIndex) {
    const colors = [
        '#1f77b4', // blue
        '#ff7f0e', // orange
        '#2ca02c', // green
        '#d62728', // red
        '#9467bd', // purple
        '#8c564b'  // brown
    ];
    
    return colors[clusterIndex % colors.length];
}

// Get suggested action text for customer segment
function getSegmentActionText(clusterIndex, avgTotal, avgQuantity) {
    if (avgTotal > 100) {
        return 'High value customers. Offer premium promotions.';
    } else if (avgQuantity > 5) {
        return 'Bulk buyers. Offer volume discounts.';
    } else if (avgTotal < 50) {
        return 'Low spenders. Offer entry-level products.';
    } else {
        return 'Average customers. General marketing approach.';
    }
}

// Get action color for segment
function getSegmentActionColor(clusterIndex) {
    const colors = ['success', 'warning', 'info', 'danger', 'primary', 'secondary'];
    return colors[clusterIndex % colors.length];
}

// Fetch and display correlation analysis
function fetchCorrelationAnalysis() {
    // Get current filter values
    const filters = getAnalysisFilterValues();
    
    // Call API to get data
    fetch('/api/filter-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filters: filters.filters,
            encoding: filters.encoding
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayCorrelationAnalysis(data.filtered_sample);
        } else {
            handleAnalysisError(data.error || 'Failed to perform correlation analysis');
        }
        document.getElementById('analysisLoadingOverlay').style.display = 'none';
    })
    .catch(error => {
        handleAnalysisError(`Error in correlation analysis: ${error.message}`);
        document.getElementById('analysisLoadingOverlay').style.display = 'none';
    });
}

// Display correlation analysis
function displayCorrelationAnalysis(data) {
    if (!data || data.length === 0) {
        document.getElementById('correlationHeatmap').innerHTML = 
            '<div class="alert alert-warning">No data available for correlation analysis</div>';
        return;
    }
    
    // Extract numeric columns
    const numericData = {};
    const firstRow = data[0];
    
    Object.keys(firstRow).forEach(key => {
        const values = data.map(row => {
            const val = row[key];
            return isNaN(parseFloat(val)) ? null : parseFloat(val);
        }).filter(val => val !== null);
        
        if (values.length > 0) {
            numericData[key] = values;
        }
    });
    
    const numericColumns = Object.keys(numericData);
    
    if (numericColumns.length < 2) {
        document.getElementById('correlationHeatmap').innerHTML = 
            '<div class="alert alert-warning">Not enough numeric columns for correlation analysis</div>';
        return;
    }
    
    // Calculate correlation matrix
    const correlationMatrix = {};
    numericColumns.forEach(col1 => {
        correlationMatrix[col1] = {};
        numericColumns.forEach(col2 => {
            correlationMatrix[col1][col2] = calculateCorrelation(numericData[col1], numericData[col2]);
        });
    });
    
    // Prepare data for heatmap
    const z = numericColumns.map(col1 => 
        numericColumns.map(col2 => correlationMatrix[col1][col2])
    );
    
    // Create heatmap
    const heatmapData = [{
        z: z,
        x: numericColumns,
        y: numericColumns,
        type: 'heatmap',
        colorscale: 'RdBu',
        reversescale: true,
        zmin: -1,
        zmax: 1,
        text: z.map((row, i) => 
            row.map((val, j) => `${numericColumns[i]} vs ${numericColumns[j]}: ${val.toFixed(2)}`)
        ),
        hoverinfo: 'text'
    }];
    
    const layout = {
        title: 'Correlation Matrix',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            color: '#fff'
        },
        xaxis: {
            tickangle: -45
        },
        yaxis: {
            automargin: true
        },
        margin: {
            l: 100,
            r: 20,
            t: 50,
            b: 100
        },
        annotations: []
    };
    
    // Add correlation values as annotations
    numericColumns.forEach((col1, i) => {
        numericColumns.forEach((col2, j) => {
            const correlation = correlationMatrix[col1][col2];
            
            // Add annotation for each cell
            layout.annotations.push({
                x: col2,
                y: col1,
                text: correlation.toFixed(2),
                font: {
                    color: Math.abs(correlation) > 0.5 ? 'white' : 'black'
                },
                showarrow: false
            });
        });
    });
    
    Plotly.newPlot('correlationHeatmap', heatmapData, layout);
    
    // Display correlation insights
    const insightsContainer = document.getElementById('correlationInsights');
    insightsContainer.innerHTML = '<h4 class="h6 mb-3">Key Insights</h4>';
    
    // Find strong correlations
    const strongCorrelations = [];
    numericColumns.forEach((col1, i) => {
        numericColumns.forEach((col2, j) => {
            if (i < j) { // Only check pairs once
                const correlation = correlationMatrix[col1][col2];
                if (Math.abs(correlation) > 0.5) {
                    strongCorrelations.push({
                        col1,
                        col2,
                        correlation
                    });
                }
            }
        });
    });
    
    // Sort by absolute correlation strength
    strongCorrelations.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));
    
    // Display strong correlations
    if (strongCorrelations.length > 0) {
        // Create insights cards
        strongCorrelations.slice(0, 3).forEach(corr => {
            const type = corr.correlation > 0 ? 'positive' : 'negative';
            const strength = Math.abs(corr.correlation) > 0.7 ? 'strong' : 'moderate';
            const color = corr.correlation > 0 ? 'success' : 'danger';
            
            const card = document.createElement('div');
            card.className = `alert alert-${color} mb-2`;
            card.innerHTML = `
                <h5 class="alert-heading">
                    <i class="fas fa-${corr.correlation > 0 ? 'arrow-up' : 'arrow-down'} me-2"></i>
                    ${strength.charAt(0).toUpperCase() + strength.slice(1)} ${type} correlation: ${Math.abs(corr.correlation).toFixed(2)}
                </h5>
                <p><strong>${corr.col1}</strong> and <strong>${corr.col2}</strong> are ${type}ly correlated.</p>
                <p class="mb-0">
                    <strong>Business implication:</strong> ${getCorrelationInsight(corr.col1, corr.col2, corr.correlation)}
                </p>
            `;
            
            insightsContainer.appendChild(card);
        });
    } else {
        insightsContainer.innerHTML += '<div class="alert alert-info">No strong correlations found in the data.</div>';
    }
}

// Calculate Pearson correlation coefficient
function calculateCorrelation(arr1, arr2) {
    if (arr1.length !== arr2.length) {
        throw new Error('Arrays must have the same length');
    }
    
    const n = arr1.length;
    
    // Calculate means
    const mean1 = arr1.reduce((sum, val) => sum + val, 0) / n;
    const mean2 = arr2.reduce((sum, val) => sum + val, 0) / n;
    
    // Calculate covariance and variances
    let cov = 0;
    let var1 = 0;
    let var2 = 0;
    
    for (let i = 0; i < n; i++) {
        const diff1 = arr1[i] - mean1;
        const diff2 = arr2[i] - mean2;
        cov += diff1 * diff2;
        var1 += diff1 * diff1;
        var2 += diff2 * diff2;
    }
    
    // Calculate correlation coefficient
    if (var1 === 0 || var2 === 0) {
        return 0; // No variation, correlation is undefined
    }
    
    return cov / Math.sqrt(var1 * var2);
}

// Get business insight text for correlation
function getCorrelationInsight(col1, col2, correlation) {
    const columns = [col1.toLowerCase(), col2.toLowerCase()];
    
    if (columns.includes('total') && columns.includes('quantity')) {
        if (correlation > 0) {
            return 'Higher quantities lead to higher sales. Consider volume-based discounts.';
        } else {
            return 'Higher quantities associated with lower totals. Review pricing strategy.';
        }
    } else if (columns.includes('total') && columns.includes('unit price')) {
        if (correlation > 0) {
            return 'Higher priced items drive more revenue. Focus on premium products.';
        } else {
            return 'Lower priced items may be more popular. Consider promotional pricing.';
        }
    } else if (columns.some(col => col.includes('rating')) && columns.includes('total')) {
        if (correlation > 0) {
            return 'Better ratings correlate with higher sales. Focus on quality improvement.';
        } else {
            return 'Ratings don\'t positively impact sales. Investigate other factors.';
        }
    } else {
        if (correlation > 0) {
            return `As ${col1} increases, ${col2} tends to increase as well.`;
        } else {
            return `As ${col1} increases, ${col2} tends to decrease.`;
        }
    }
}

// Fetch and display product analysis
function fetchProductAnalysis() {
    // Get current filter values
    const filters = getAnalysisFilterValues();
    
    // Call API to generate charts
    fetch('/api/generate-chart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            chart_type: 'product_analysis',
            filters: filters.filters,
            encoding: filters.encoding
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayProductAnalysis(data.chart_data);
        } else {
            handleAnalysisError(data.error || 'Failed to perform product analysis');
        }
        document.getElementById('analysisLoadingOverlay').style.display = 'none';
    })
    .catch(error => {
        handleAnalysisError(`Error in product analysis: ${error.message}`);
        document.getElementById('analysisLoadingOverlay').style.display = 'none';
    });
}

// Display product analysis
function displayProductAnalysis(chartData) {
    if (!chartData || !chartData.price || !chartData.quantity) {
        document.getElementById('categoryPerformanceChart').innerHTML = 
            '<div class="alert alert-warning">Insufficient data for product analysis</div>';
        document.getElementById('categoryQuantityChart').innerHTML = '';
        document.getElementById('productMatrix').innerHTML = '';
        return;
    }
    
    // Price chart
    const priceChartData = [{
        x: chartData.price.x,
        y: chartData.price.y,
        type: 'bar',
        marker: {
            color: 'rgba(0, 123, 255, 0.7)',
            line: {
                color: 'rgba(0, 123, 255, 1.0)',
                width: 2
            }
        }
    }];
    
    const priceLayout = {
        title: chartData.price.title,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            color: '#fff'
        },
        xaxis: {
            title: 'Product Category',
            gridcolor: 'rgba(255,255,255,0.1)',
            tickangle: -45
        },
        yaxis: {
            title: 'Average Unit Price',
            gridcolor: 'rgba(255,255,255,0.1)'
        }
    };
    
    Plotly.newPlot('categoryPerformanceChart', priceChartData, priceLayout);
    
    // Quantity chart
    const quantityChartData = [{
        x: chartData.quantity.x,
        y: chartData.quantity.y,
        type: 'bar',
        marker: {
            color: 'rgba(40, 167, 69, 0.7)',
            line: {
                color: 'rgba(40, 167, 69, 1.0)',
                width: 2
            }
        }
    }];
    
    const quantityLayout = {
        title: chartData.quantity.title,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            color: '#fff'
        },
        xaxis: {
            title: 'Product Category',
            gridcolor: 'rgba(255,255,255,0.1)',
            tickangle: -45
        },
        yaxis: {
            title: 'Quantity Sold',
            gridcolor: 'rgba(255,255,255,0.1)'
        }
    };
    
    Plotly.newPlot('categoryQuantityChart', quantityChartData, quantityLayout);
    
    // Product performance matrix
    const tableBody = document.querySelector('#productMatrix tbody');
    tableBody.innerHTML = '';
    
    // Combine data for the table
    const categories = chartData.price.x;
    const prices = chartData.price.y;
    const quantities = chartData.quantity.y;
    
    // Calculate totals (price * quantity)
    const totals = prices.map((price, i) => price * quantities[i]);
    
    // Create table rows
    categories.forEach((category, i) => {
        const tr = document.createElement('tr');
        
        const tdCategory = document.createElement('td');
        tdCategory.textContent = category;
        
        const tdSales = document.createElement('td');
        tdSales.textContent = formatCurrency(totals[i]);
        
        const tdQuantity = document.createElement('td');
        tdQuantity.textContent = quantities[i];
        
        const tdPrice = document.createElement('td');
        tdPrice.textContent = formatCurrency(prices[i]);
        
        const tdPerformance = document.createElement('td');
        const performance = getPerformanceRating(totals[i], quantities[i], prices[i]);
        tdPerformance.innerHTML = `<span class="badge bg-${performance.color}">${performance.rating}</span>`;
        
        tr.appendChild(tdCategory);
        tr.appendChild(tdSales);
        tr.appendChild(tdQuantity);
        tr.appendChild(tdPrice);
        tr.appendChild(tdPerformance);
        
        tableBody.appendChild(tr);
    });
}

// Get performance rating for product category
function getPerformanceRating(total, quantity, price) {
    // This is a simplified rating system
    // In a real application, you'd compare against benchmarks
    
    if (total > 1000 && quantity > 50) {
        return { rating: 'High Performer', color: 'success' };
    } else if (total > 500 || quantity > 30) {
        return { rating: 'Good Performer', color: 'info' };
    } else if (price > 50) {
        return { rating: 'Premium', color: 'primary' };
    } else if (total < 200 && quantity < 10) {
        return { rating: 'Under Performer', color: 'danger' };
    } else {
        return { rating: 'Average', color: 'secondary' };
    }
}

// Fetch and display time analysis
function fetchTimeAnalysis() {
    // Get current filter values
    const filters = getAnalysisFilterValues();
    
    // Call API for hourly distribution
    fetch('/api/generate-chart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            chart_type: 'sales_heatmap',
            filters: filters.filters,
            encoding: filters.encoding
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // First handle the heatmap data
            displayTimeHeatmap(data.chart_data);
            
            // Now fetch hourly distribution
            return fetch('/api/generate-chart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    chart_type: 'time_series',
                    filters: filters.filters,
                    encoding: filters.encoding
                })
            });
        } else {
            handleAnalysisError(data.error || 'Failed to perform time analysis');
            throw new Error('Failed to fetch heatmap data');
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Display hourly and day of week distributions
            displayHourlyDistribution(data.chart_data);
        } else {
            handleAnalysisError(data.error || 'Failed to fetch hourly distribution data');
        }
        document.getElementById('analysisLoadingOverlay').style.display = 'none';
    })
    .catch(error => {
        handleAnalysisError(`Error in time analysis: ${error.message}`);
        document.getElementById('analysisLoadingOverlay').style.display = 'none';
    });
}

// Display time heatmap
function displayTimeHeatmap(chartData) {
    if (!chartData || !chartData.z || !chartData.x || !chartData.y) {
        document.getElementById('timeHeatmapChart').innerHTML = 
            '<div class="alert alert-warning">Insufficient data for time heatmap</div>';
        return;
    }
    
    const data = [{
        z: chartData.z,
        x: chartData.x,
        y: chartData.y,
        type: 'heatmap',
        colorscale: 'Viridis',
        showscale: true,
        hovertemplate: 'Day: %{y}<br>Hour: %{x}<br>Sales: %{z}<extra></extra>'
    }];
    
    const layout = {
        title: chartData.title || 'Sales Heatmap by Day and Hour',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            color: '#fff'
        },
        xaxis: {
            title: 'Hour of Day',
            dtick: 2 // Show every other hour
        },
        yaxis: {
            title: 'Day of Week'
        },
        margin: {
            l: 100,
            r: 80,
            t: 50,
            b: 50
        }
    };
    
    Plotly.newPlot('timeHeatmapChart', data, layout);
}

// Display hourly distribution
function displayHourlyDistribution(chartData) {
    if (!chartData || !chartData.x || !chartData.y) {
        document.getElementById('hourlyDistributionChart').innerHTML = 
            '<div class="alert alert-warning">Insufficient data for hourly distribution</div>';
        document.getElementById('dayOfWeekChart').innerHTML = 
            '<div class="alert alert-warning">Insufficient data for day of week distribution</div>';
        return;
    }
    
    // For this demo, we'll create a simulated hourly distribution since the API
    // returns daily data. In a production environment, you would use real hourly data.
    
    // Create hourly distribution
    const hours = Array.from({length: 24}, (_, i) => i);
    const hourValues = hours.map(hour => {
        // Generate a distribution that peaks in the afternoon
        const base = 100;
        if (hour < 6) return base * 0.2; // Early morning
        if (hour < 10) return base * 0.5 + Math.random() * 30; // Morning
        if (hour < 14) return base * 1.0 + Math.random() * 50; // Lunch
        if (hour < 19) return base * 1.2 + Math.random() * 40; // Afternoon/Evening
        return base * 0.7 + Math.random() * 20; // Night
    });
    
    const hourlyData = [{
        x: hours,
        y: hourValues,
        type: 'bar',
        marker: {
            color: 'rgba(75, 192, 192, 0.7)',
            line: {
                color: 'rgba(75, 192, 192, 1.0)',
                width: 2
            }
        }
    }];
    
    const hourlyLayout = {
        title: 'Sales by Hour of Day',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            color: '#fff'
        },
        xaxis: {
            title: 'Hour of Day',
            tickvals: hours,
            gridcolor: 'rgba(255,255,255,0.1)'
        },
        yaxis: {
            title: 'Sales',
            gridcolor: 'rgba(255,255,255,0.1)'
        }
    };
    
    Plotly.newPlot('hourlyDistributionChart', hourlyData, hourlyLayout);
    
    // Create day of week distribution
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const dayValues = days.map(() => Math.random() * 1000 + 500); // Random values for this demo
    
    const dayData = [{
        x: days,
        y: dayValues,
        type: 'bar',
        marker: {
            color: 'rgba(255, 159, 64, 0.7)',
            line: {
                color: 'rgba(255, 159, 64, 1.0)',
                width: 2
            }
        }
    }];
    
    const dayLayout = {
        title: 'Sales by Day of Week',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            color: '#fff'
        },
        xaxis: {
            title: 'Day of Week',
            gridcolor: 'rgba(255,255,255,0.1)'
        },
        yaxis: {
            title: 'Sales',
            gridcolor: 'rgba(255,255,255,0.1)'
        }
    };
    
    Plotly.newPlot('dayOfWeekChart', dayData, dayLayout);
}

// Fetch and display business insights
function fetchInsights() {
    // Safely get elements with null checks
    const insightsMessage = document.getElementById('insightsMessage');
    const insightsSpinner = document.getElementById('insightsSpinner');
    const analysisLoadingOverlay = document.getElementById('analysisLoadingOverlay');
    
    // Safely update elements if they exist
    if (insightsMessage) {
        insightsMessage.textContent = 'Analyzing data...';
    }
    
    if (insightsSpinner) {
        insightsSpinner.style.display = 'block';
    }
    
    // Get current filter values
    const filters = getAnalysisFilterValues();

    // Use POST method to ensure proper handling of filter parameters
    fetch('/api/generate-insights', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filters: filters.filters,
            encoding: filters.encoding
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayBusinessInsights(data.insights);
            } else {
                handleAnalysisError(data.error || 'Failed to generate insights');
            }
            
            // Safely hide elements if they exist
            if (insightsSpinner) {
                insightsSpinner.style.display = 'none';
            }
            
            if (analysisLoadingOverlay) {
                analysisLoadingOverlay.style.display = 'none';
            }
        })
        .catch(error => {
            handleAnalysisError(`Error generating insights: ${error.message}`);
            
            // Safely hide elements if they exist
            if (insightsSpinner) {
                insightsSpinner.style.display = 'none';
            }
            
            if (analysisLoadingOverlay) {
                analysisLoadingOverlay.style.display = 'none';
            }
        });
}

// Display business insights
function displayBusinessInsights(insights) {
    const insightsContainer = document.getElementById('insightsContainer');
    
    // Check if container exists
    if (!insightsContainer) {
        console.error('Error: insightsContainer element not found');
        return;
    }
    
    if (!insights || insights.length === 0) {
        insightsContainer.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                No insights could be generated from the available data.
            </div>
        `;
        return;
    }
    
    insightsContainer.innerHTML = '';
    
    // Create a card for each insight
    insights.forEach((insight, index) => {
        const card = document.createElement('div');
        card.className = 'insight-card card bg-dark mb-3';
        
        // Add default icon in case getInsightIcon fails
        let icon = { class: 'fas fa-info-circle', color: 'info' };
        try {
            icon = getInsightIcon(insight) || icon;
        } catch (e) {
            console.error('Error getting insight icon:', e);
        }
        
        card.innerHTML = `
            <div class="card-body">
                <div class="d-flex align-items-start">
                    <div class="me-3">
                        <i class="${icon.class} fa-2x text-${icon.color}"></i>
                    </div>
                    <div>
                        <div class="markdown-content">${insight}</div>
                    </div>
                </div>
            </div>
        `;
        
        insightsContainer.appendChild(card);
    });
}

// Get icon for insight based on content
function getInsightIcon(insight) {
    // Check if insight is a valid string before processing
    if (!insight || typeof insight !== 'string') {
        return { class: 'fas fa-info-circle', color: 'info' };
    }
    
    try {
        if (insight.includes('⭐')) {
            return { class: 'fas fa-star', color: 'warning' };
        } else if (insight.includes('⚠️')) {
            return { class: 'fas fa-exclamation-triangle', color: 'danger' };
        } else if (insight.includes('📈')) {
            return { class: 'fas fa-chart-line', color: 'success' };
        } else if (insight.includes('📉')) {
            return { class: 'fas fa-chart-line', color: 'danger' };
        } else if (insight.includes('⏱️')) {
            return { class: 'fas fa-clock', color: 'info' };
        } else if (insight.includes('🐢')) {
            return { class: 'fas fa-hourglass-half', color: 'secondary' };
        } else if (insight.includes('🔗')) {
            return { class: 'fas fa-link', color: 'primary' };
        } else if (insight.includes('🎯')) {
            return { class: 'fas fa-bullseye', color: 'danger' };
        } else if (insight.includes('🛒')) {
            return { class: 'fas fa-shopping-cart', color: 'success' };
        } else if (insight.includes('📊')) {
            return { class: 'fas fa-chart-bar', color: 'primary' };
        } else {
            return { class: 'fas fa-lightbulb', color: 'warning' };
        }
    } catch (error) {
        console.error('Error processing insight for icon:', error);
        return { class: 'fas fa-info-circle', color: 'info' };
    }
}

// Generate a sales forecast
function generateSalesForecast() {
    // Show loading overlay
    document.getElementById('forecastLoadingOverlay').style.display = 'flex';
    
    // Get form values
    const periods = document.getElementById('forecastPeriods').value;
    const yearlySeasonality = document.getElementById('yearlySeasonality').checked;
    const weeklySeasonality = document.getElementById('weeklySeasonality').checked;
    const dailySeasonality = document.getElementById('dailySeasonality').checked;
    const encoding = document.getElementById('encodingForecast').value;
    
    // Get filter values
    const category = document.getElementById('categoryFilterForecast').value;
    const customerType = document.getElementById('customerTypeFilterForecast').value;
    const startDate = document.getElementById('startDateForecast').value;
    const endDate = document.getElementById('endDateForecast').value;
    
    // Prepare request body
    const requestBody = {
        periods: parseInt(periods),
        encoding: encoding,
        yearly_seasonality: yearlySeasonality,
        weekly_seasonality: weeklySeasonality,
        daily_seasonality: dailySeasonality,
        filters: {
            category: category,
            customer_type: customerType,
            date_range: [startDate, endDate].filter(Boolean)
        }
    };
    
    // Call API to generate forecast
    fetch('/api/sales-forecast', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayForecast(data);
            document.getElementById('downloadForecastBtn').disabled = false;
        } else {
            showForecastError(data.error || 'Failed to generate forecast');
        }
        document.getElementById('forecastLoadingOverlay').style.display = 'none';
    })
    .catch(error => {
        showForecastError('Error generating forecast: ' + error);
        document.getElementById('forecastLoadingOverlay').style.display = 'none';
    });
}

// Display forecast results
function displayForecast(data) {
    // Hide message and show chart
    document.getElementById('forecastMessage').style.display = 'none';
    document.getElementById('forecastChartContainer').style.display = 'block';
    document.getElementById('forecastStatsRow').style.display = 'flex';
    document.getElementById('forecastComponentsCard').style.display = 'block';
    document.getElementById('forecastInsightsCard').style.display = 'block';
    
    // Create forecast chart
    const forecastData = data.forecast;
    
    // Calculate actual vs predicted stats
    const actualValues = forecastData.y.filter(v => v > 0);
    const predictedValues = forecastData.yhat.slice(0, actualValues.length);
    
    // Calculate average forecasted sales
    const avgHistorical = actualValues.reduce((sum, val) => sum + val, 0) / actualValues.length;
    const avgForecast = forecastData.yhat.slice(-data.periods).reduce((sum, val) => sum + val, 0) / data.periods;
    const percentChange = ((avgForecast - avgHistorical) / avgHistorical) * 100;
    
    // Update stats
    document.getElementById('avgForecastSales').textContent = avgForecast.toFixed(2);
    const avgForecastDiff = document.getElementById('avgForecastDiff');
    avgForecastDiff.textContent = `${percentChange >= 0 ? '+' : ''}${percentChange.toFixed(2)}%`;
    avgForecastDiff.className = `badge rounded-pill ${percentChange >= 0 ? 'bg-success' : 'bg-danger'}`;
    
    // Find peak day
    const futureYhat = forecastData.yhat.slice(-data.periods);
    const maxIndex = futureYhat.indexOf(Math.max(...futureYhat));
    const peakDate = new Date(forecastData.ds[forecastData.ds.length - data.periods + maxIndex]);
    document.getElementById('peakForecastDay').textContent = peakDate.toLocaleDateString();
    document.getElementById('peakForecastValue').textContent = Math.max(...futureYhat).toFixed(2);
    
    // Calculate simple accuracy metric (lower is better)
    let mape = 0;
    if (actualValues.length > 0) {
        const absPctErrors = actualValues.map((actual, i) => 
            Math.abs((actual - predictedValues[i]) / (actual === 0 ? 1 : actual)) * 100
        );
        mape = absPctErrors.reduce((sum, val) => sum + val, 0) / absPctErrors.length;
        const accuracy = Math.max(0, 100 - mape).toFixed(1);
        document.getElementById('forecastAccuracy').textContent = `${accuracy}%`;
        document.getElementById('accuracyDetails').textContent = `MAPE: ${mape.toFixed(2)}%`;
    } else {
        document.getElementById('forecastAccuracy').textContent = 'N/A';
        document.getElementById('accuracyDetails').textContent = 'Insufficient historical data';
    }
    
    // Create forecast chart
    const trace1 = {
        x: forecastData.ds,
        y: forecastData.y,
        mode: 'markers',
        name: 'Historical',
        marker: {
            color: 'rgba(255, 255, 255, 0.8)',
            size: 5
        }
    };
    
    const trace2 = {
        x: forecastData.ds,
        y: forecastData.yhat,
        mode: 'lines',
        name: 'Forecast',
        line: {
            color: 'rgba(0, 123, 255, 1)',
            width: 2
        }
    };
    
    const trace3 = {
        x: forecastData.ds,
        y: forecastData.yhat_upper,
        mode: 'lines',
        name: 'Upper Bound',
        line: {
            color: 'rgba(0, 123, 255, 0.3)',
            width: 0
        },
        fill: 'tonexty'
    };
    
    const trace4 = {
        x: forecastData.ds,
        y: forecastData.yhat_lower,
        mode: 'lines',
        name: 'Lower Bound',
        line: {
            color: 'rgba(0, 123, 255, 0.3)',
            width: 0
        },
        fill: 'tonexty'
    };
    
    const layout = {
        title: 'Sales Forecast',
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
            title: 'Sales',
            gridcolor: 'rgba(255,255,255,0.1)'
        },
        legend: {
            orientation: 'h',
            y: -0.2
        },
        margin: {
            l: 60,
            r: 30,
            t: 50,
            b: 80
        }
    };
    
    Plotly.newPlot('forecastChart', [trace1, trace2, trace3, trace4], layout);
    
    // Display components if available
    if (data.components) {
        // Trend component
        if (data.components.trend) {
            const trendTrace = {
                x: data.components.trend.x,
                y: data.components.trend.y,
                mode: 'lines',
                name: 'Trend',
                line: {
                    color: 'rgba(255, 193, 7, 1)',
                    width: 2
                }
            };
            
            const trendLayout = {
                title: 'Trend Component',
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
                    title: 'Trend Value',
                    gridcolor: 'rgba(255,255,255,0.1)'
                },
                margin: {
                    l: 60,
                    r: 30,
                    t: 50,
                    b: 50
                }
            };
            
            Plotly.newPlot('trendComponent', [trendTrace], trendLayout);
        }
        
        // Weekly component
        if (data.components.weekly) {
            const weeklyTrace = {
                x: data.components.weekly.x,
                y: data.components.weekly.y,
                type: 'bar',
                name: 'Weekly Pattern',
                marker: {
                    color: 'rgba(13, 202, 240, 0.8)'
                }
            };
            
            const weeklyLayout = {
                title: 'Weekly Seasonality Component',
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: {
                    color: '#fff'
                },
                xaxis: {
                    title: 'Day of Week',
                    gridcolor: 'rgba(255,255,255,0.1)'
                },
                yaxis: {
                    title: 'Effect on Sales',
                    gridcolor: 'rgba(255,255,255,0.1)'
                },
                margin: {
                    l: 60,
                    r: 30,
                    t: 50,
                    b: 50
                }
            };
            
            Plotly.newPlot('weeklyComponent', [weeklyTrace], weeklyLayout);
        }
    }
    
    // Generate insights
    generateForecastInsights(data);
}

// Generate forecast insights
function generateForecastInsights(data) {
    const insightsContainer = document.getElementById('forecastInsights');
    insightsContainer.innerHTML = '';
    
    const forecast = data.forecast;
    const periods = data.periods;
    
    // Calculate trends
    const futureYhat = forecast.yhat.slice(-periods);
    const avgForecast = futureYhat.reduce((sum, val) => sum + val, 0) / periods;
    
    const actualValues = forecast.y.filter(v => v > 0);
    const avgHistorical = actualValues.reduce((sum, val) => sum + val, 0) / actualValues.length;
    
    const percentChange = ((avgForecast - avgHistorical) / avgHistorical) * 100;
    
    // Find peak and trough days
    const maxIndex = futureYhat.indexOf(Math.max(...futureYhat));
    const minIndex = futureYhat.indexOf(Math.min(...futureYhat));
    
    const peakDate = new Date(forecast.ds[forecast.ds.length - periods + maxIndex]);
    const troughDate = new Date(forecast.ds[forecast.ds.length - periods + minIndex]);
    
    // Generate insights
    const insights = [];
    
    // Overall trend
    if (percentChange > 10) {
        insights.push(`
            <div class="alert alert-success">
                <h5><i class="fas fa-arrow-up me-2"></i>Strong Growth Trend</h5>
                <p>Sales are forecasted to increase by <strong>${percentChange.toFixed(1)}%</strong> over the next ${periods} days compared to historical average.</p>
                <p><strong>Recommendation:</strong> Ensure inventory levels are increased to meet growing demand.</p>
            </div>
        `);
    } else if (percentChange > 0) {
        insights.push(`
            <div class="alert alert-info">
                <h5><i class="fas fa-arrow-up me-2"></i>Moderate Growth Trend</h5>
                <p>Sales are forecasted to increase by <strong>${percentChange.toFixed(1)}%</strong> over the next ${periods} days.</p>
                <p><strong>Recommendation:</strong> Maintain current inventory levels and monitor growth.</p>
            </div>
        `);
    } else if (percentChange > -10) {
        insights.push(`
            <div class="alert alert-warning">
                <h5><i class="fas fa-arrow-down me-2"></i>Slight Decline Trend</h5>
                <p>Sales are forecasted to decrease by <strong>${Math.abs(percentChange).toFixed(1)}%</strong> over the next ${periods} days.</p>
                <p><strong>Recommendation:</strong> Consider light promotions to boost sales.</p>
            </div>
        `);
    } else {
        insights.push(`
            <div class="alert alert-danger">
                <h5><i class="fas fa-arrow-down me-2"></i>Significant Decline Trend</h5>
                <p>Sales are forecasted to decrease by <strong>${Math.abs(percentChange).toFixed(1)}%</strong> over the next ${periods} days.</p>
                <p><strong>Recommendation:</strong> Implement promotional campaigns and review pricing strategies.</p>
            </div>
        `);
    }
    
    // Peak and trough days
    insights.push(`
        <div class="alert alert-light">
            <h5><i class="fas fa-calendar-alt me-2"></i>Key Dates</h5>
            <ul class="mb-0">
                <li><strong>Peak sales day:</strong> ${peakDate.toLocaleDateString()} (${forecast.yhat[forecast.ds.length - periods + maxIndex].toFixed(2)})</li>
                <li><strong>Lowest sales day:</strong> ${troughDate.toLocaleDateString()} (${forecast.yhat[forecast.ds.length - periods + minIndex].toFixed(2)})</li>
            </ul>
            <p class="mt-2"><strong>Recommendation:</strong> Ensure adequate staffing on peak days and consider promotions during slow periods.</p>
        </div>
    `);
    
    // Volatility insight
    const stdDev = calculateStandardDeviation(futureYhat);
    const volatility = (stdDev / avgForecast) * 100;
    
    if (volatility > 20) {
        insights.push(`
            <div class="alert alert-warning">
                <h5><i class="fas fa-exclamation-triangle me-2"></i>High Sales Volatility</h5>
                <p>The forecast shows high volatility (${volatility.toFixed(1)}%) in daily sales over the next ${periods} days.</p>
                <p><strong>Recommendation:</strong> Prepare for fluctuating demand and maintain flexible staffing.</p>
            </div>
        `);
    } else if (volatility < 10) {
        insights.push(`
            <div class="alert alert-info">
                <h5><i class="fas fa-check-circle me-2"></i>Stable Sales Pattern</h5>
                <p>The forecast shows stable daily sales with low volatility (${volatility.toFixed(1)}%) over the next ${periods} days.</p>
                <p><strong>Recommendation:</strong> Maintain consistent inventory and staffing levels.</p>
            </div>
        `);
    }
    
    // Render insights
    insightsContainer.innerHTML = insights.join('');
}

// Calculate standard deviation of an array
function calculateStandardDeviation(values) {
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const squareDiffs = values.map(value => {
        const diff = value - mean;
        return diff * diff;
    });
    const avgSquareDiff = squareDiffs.reduce((sum, val) => sum + val, 0) / squareDiffs.length;
    return Math.sqrt(avgSquareDiff);
}

// Show forecast error
function showForecastError(message) {
    document.getElementById('forecastMessage').style.display = 'block';
    document.getElementById('forecastChartContainer').style.display = 'none';
    document.getElementById('forecastStatsRow').style.display = 'none';
    document.getElementById('forecastComponentsCard').style.display = 'none';
    document.getElementById('forecastInsightsCard').style.display = 'none';
    
    document.getElementById('forecastMessage').innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-circle me-2"></i>${message}
        </div>
    `;
}

// Download forecast data as CSV
function downloadForecastData() {
    // Implementation would depend on your data structure
    // This is a simplified example
    alert('Forecast data download functionality would be implemented here');
}

// Helper function to get analysis filter values
function getAnalysisFilterValues() {
    const category = document.getElementById('categoryFilterAnalysis')?.value || 'All';
    const customerType = document.getElementById('customerTypeFilterAnalysis')?.value || 'All';
    const gender = document.getElementById('genderFilterAnalysis')?.value || 'All';
    const startDate = document.getElementById('startDateAnalysis')?.value || '';
    const endDate = document.getElementById('endDateAnalysis')?.value || '';
    const encoding = 'utf-8';
    
    const filters = {
        category: category,
        customer_type: customerType,
        gender: gender
    };
    
    if (startDate && endDate) {
        filters.date_range = [startDate, endDate];
    }
    
    return {
        filters: filters,
        encoding: encoding
    };
}

// Setup churn prediction
function setupChurnPrediction() {
    console.log('Setting up churn prediction tab...');
    
    // Set up the churn prediction button
    const runChurnPredictionBtn = document.getElementById('runChurnPredictionBtn');
    if (runChurnPredictionBtn) {
        runChurnPredictionBtn.removeEventListener('click', performChurnPrediction);
        runChurnPredictionBtn.addEventListener('click', performChurnPrediction);
    }
    
    // Hide loading overlay
    document.getElementById('analysisLoadingOverlay').style.display = 'none';
}

// Perform churn prediction
function performChurnPrediction() {
    console.log('Performing churn prediction...');
    
    // Show loading state
    document.getElementById('churnContainer').style.display = 'none';
    document.getElementById('churnErrorState').style.display = 'none';
    document.getElementById('churnLoadingState').style.display = 'block';
    
    // Get filter values using the existing function
    const filterData = getAnalysisFilterValues();
    
    // Call API endpoint
    fetch('/api/churn-prediction', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(filterData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'An error occurred during churn prediction');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success && data.churn_data) {
            displayChurnResults(data.churn_data);
        } else {
            throw new Error('Invalid response from server');
        }
    })
    .catch(error => {
        console.error('Churn prediction error:', error);
        document.getElementById('churnErrorMessage').textContent = error.message || 'Failed to perform churn analysis';
        document.getElementById('churnErrorState').style.display = 'block';
    })
    .finally(() => {
        document.getElementById('churnLoadingState').style.display = 'none';
        document.getElementById('churnContainer').style.display = 'block';
    });
}

// Display churn prediction results
function displayChurnResults(churnData) {
    console.log('Displaying churn results:', churnData);
    
    // Format churn rate
    const churnRate = churnData.churn_rate * 100;
    document.getElementById('churnRateDisplay').textContent = `${churnRate.toFixed(1)}%`;
    document.getElementById('churnRateProgress').style.width = `${churnRate}%`;
    
    // Customer counts
    document.getElementById('churnCount').textContent = churnData.churn_count;
    document.getElementById('retainedCount').textContent = churnData.total_customers - churnData.churn_count;
    
    // Model performance
    document.getElementById('modelAccuracy').textContent = `${(churnData.accuracy * 100).toFixed(1)}%`;
    document.getElementById('modelDataSize').textContent = `Based on ${churnData.test_size} samples`;
    
    // Feature importance chart
    if (churnData.features && churnData.importances) {
        const features = churnData.features;
        const importances = churnData.importances;
        
        // Create sorted arrays for visualization
        const featureData = features.map((feature, index) => ({
            feature: feature,
            importance: importances[index]
        })).sort((a, b) => b.importance - a.importance);
        
        // Create Plotly bar chart
        const plotlyData = [{
            x: featureData.map(d => d.importance),
            y: featureData.map(d => d.feature),
            type: 'bar',
            orientation: 'h',
            marker: {
                color: 'rgba(55, 128, 191, 0.8)',
                line: {
                    color: 'rgba(55, 128, 191, 1.0)',
                    width: 1
                }
            }
        }];
        
        const layout = {
            margin: { l: 150, r: 20, t: 10, b: 50 },
            xaxis: { title: 'Importance' },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#c9d1d9' }
        };
        
        Plotly.newPlot('featureImportanceChart', plotlyData, layout);
    }
    
    // Customer count pie chart
    const customerChartData = [{
        values: [churnData.churn_count, churnData.total_customers - churnData.churn_count],
        labels: ['At Risk', 'Retained'],
        type: 'pie',
        marker: {
            colors: ['#dc3545', '#198754']
        },
        textinfo: 'percent',
        hole: 0.4
    }];
    
    const customerChartLayout = {
        margin: { l: 10, r: 10, t: 0, b: 0 },
        showlegend: false,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#c9d1d9' }
    };
    
    Plotly.newPlot('customerCountChart', customerChartData, customerChartLayout);
    
    // Recommendations
    generateChurnRecommendations(churnData);
}

// Generate recommendations based on churn prediction results
function generateChurnRecommendations(churnData) {
    const recommendationsContainer = document.getElementById('churnRecommendations');
    
    // Clear previous recommendations
    recommendationsContainer.innerHTML = '';
    
    // Generate recommendations based on churn data
    const recommendations = [];
    
    // High churn rate recommendation
    if (churnData.churn_rate > 0.3) {
        recommendations.push({
            title: 'High Churn Rate Alert',
            text: `Your churn rate of ${(churnData.churn_rate * 100).toFixed(1)}% is concerning. Consider implementing a customer retention program immediately.`,
            icon: 'exclamation-triangle',
            color: 'danger'
        });
    }
    
    // Feature-based recommendations
    if (churnData.features && churnData.importances) {
        const featureData = churnData.features.map((feature, index) => ({
            feature: feature,
            importance: churnData.importances[index]
        })).sort((a, b) => b.importance - a.importance);
        
        // Top feature recommendation
        if (featureData.length > 0) {
            const topFeature = featureData[0];
            
            if (topFeature.feature === 'Days Since Last Purchase') {
                recommendations.push({
                    title: 'Re-engage Inactive Customers',
                    text: 'Time since last purchase is the strongest predictor of churn. Consider implementing a re-engagement campaign targeting customers who haven\'t purchased in the last 30-60 days.',
                    icon: 'clock',
                    color: 'warning'
                });
            } else if (topFeature.feature === 'Average Purchase Value') {
                recommendations.push({
                    title: 'Value-Based Segmentation',
                    text: 'Average purchase value strongly influences churn. Consider different retention strategies for high-value versus low-value customers.',
                    icon: 'tags',
                    color: 'primary'
                });
            } else if (topFeature.feature === 'Total') {
                recommendations.push({
                    title: 'Customer Spending Tier Program',
                    text: 'Total spending is a key churn indicator. Implement a tiered loyalty program that rewards customers based on their total spending history.',
                    icon: 'star',
                    color: 'info'
                });
            } else if (topFeature.feature === 'Quantity') {
                recommendations.push({
                    title: 'Volume-Based Incentives',
                    text: 'Purchase quantity impacts churn likelihood. Consider volume discounts or bundle offers to encourage larger purchases.',
                    icon: 'shopping-cart',
                    color: 'success'
                });
            }
        }
    }
    
    // General recommendations
    recommendations.push({
        title: 'Implement Feedback Collection',
        text: 'Regularly collect customer feedback to identify issues before they lead to churn. Focus especially on customers showing warning signs.',
        icon: 'comments',
        color: 'info'
    });
    
    // Add recommendations to container
    if (recommendations.length === 0) {
        recommendationsContainer.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No specific recommendations available based on current data.
            </div>
        `;
    } else {
        recommendations.forEach(rec => {
            recommendationsContainer.innerHTML += `
                <div class="alert alert-${rec.color} mb-2">
                    <h5 class="alert-heading"><i class="fas fa-${rec.icon} me-2"></i>${rec.title}</h5>
                    <p class="mb-0">${rec.text}</p>
                </div>
            `;
        });
    }
}

// Handle analysis errors
function handleAnalysisError(message) {
    console.error(message);
    document.getElementById('analysisLoadingOverlay').style.display = 'none';
    alert(`Error: ${message}`);
}

// Handle forecast errors
function handleForecastError(message) {
    console.error(message);
    document.getElementById('forecastLoadingOverlay').style.display = 'none';
    alert(`Error: ${message}`);
}

// Generate customer segmentation
function runCustomerSegmentation() {
    document.getElementById('analysisLoadingOverlay').style.display = 'flex';
    fetchCustomerSegmentation();
}

// Generate business insights
function generateBusinessInsights() {
    const loadingOverlay = document.getElementById('analysisLoadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
    }
    fetchInsights();
}

// Format currency values
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

