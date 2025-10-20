# Supermarket Sales Analytics Dashboard

## Overview
A stunning 3D-enhanced analytics dashboard for supermarket sales data. This comprehensive web application combines Flask backend with modern 3D visualizations, glassmorphism UI effects, and advanced analytics capabilities.

## Recent Changes (October 20, 2025)
- ✨ **3D UI Transformation**: Complete redesign with Three.js animated particle background
- 🎯 **Professional Logo**: AI-generated logo combining shopping cart with analytics graph
- 🔮 **Enhanced Header**: Glassmorphism navbar with gradient text, animated logo, and hover effects
- 💫 **Smooth Animations**: Card hover effects with optimized reveal animations
- 🎨 **Gradient Design**: Beautiful gradient text and modern color schemes
- 📊 **Enhanced Pie Charts**: Improved 3D pie charts with pull effects, gradients, and better legends
- ⚡ **Performance Optimizations**: Disabled 3D effects on analysis page, throttled scroll handlers
- 🛠️ **Fixed**: Removed conflicting parallax effects that were overwriting 3D transforms

## Project Architecture

### Frontend Stack
- **UI Framework**: Bootstrap 5 with custom dark theme
- **3D Graphics**: Three.js for animated particle background
- **Charts**: Plotly.js for interactive data visualizations
- **Styling**: Custom CSS with glassmorphism and 3D transforms
- **Icons**: Font Awesome 6.4.0

### Backend Stack
- **Framework**: Flask 2.3.3
- **Database ORM**: SQLAlchemy 2.0.28
- **Data Processing**: Pandas 2.2.3, NumPy 1.26.4
- **Analytics**: 
  - Scikit-learn 1.6.1 (Machine Learning)
  - Prophet 1.1.6 (Time Series Forecasting)
  - Seaborn 0.13.2 (Statistical Visualization)
- **Parallel App**: Streamlit 1.45.0 (Alternative UI)

### Key Features
1. **Data Upload & Processing**
   - CSV file upload with encoding support
   - Data validation and cleaning
   - Real-time data preview

2. **Sales Analytics**
   - Product category analysis
   - Payment method distribution
   - Time-based trends
   - Customer demographics

3. **Advanced Analytics**
   - Customer segmentation (K-Means clustering)
   - Churn prediction (Machine Learning)
   - Correlation analysis
   - Product-specific insights

4. **Sales Forecasting**
   - Prophet-based time series forecasting
   - Configurable forecast periods
   - Trend analysis and seasonality detection

5. **3D Visual Effects**
   - Animated particle background (Three.js)
   - Glassmorphism navbar and card effects
   - 3D hover transformations on cards (excluded from analysis page)
   - Enhanced 3D pie charts with pull effects
   - Smooth reveal animations using CSS classes
   - Gradient text and modern color schemes
   - Professional AI-generated logo with floating animation

## File Structure
```
├── app.py                  # Main Flask application
├── main.py                 # Application entry point
├── models.py               # Database models
├── api.py                  # API routes
├── config.py               # Configuration settings
├── feature.py              # ML and analytics features
├── visualise.py            # Visualization functions
├── utils.py                # Utility functions
├── streamlit_app.py        # Streamlit alternative interface
│
├── templates/              # HTML templates
│   ├── layout.html         # Base template with 3D enhancements
│   ├── index.html          # Homepage
│   ├── upload.html         # File upload page
│   ├── dashboard.html      # Main dashboard
│   ├── analysis.html       # Advanced analytics
│   └── forecast.html       # Forecasting interface
│
├── static/
│   ├── css/
│   │   ├── custom.css          # Original custom styles
│   │   ├── 3d-theme.css        # 3D effects and glassmorphism
│   │   └── header-theme.css    # Enhanced header/navbar styling
│   ├── js/
│   │   ├── dashboard.js        # Dashboard functionality with enhanced charts
│   │   ├── charts.js           # Chart generation for analysis/forecast
│   │   ├── three-background.js # Three.js 3D animated background
│   │   └── 3d-interactions.js  # 3D UI interactions (disabled on analysis)
│   └── assets/
│       ├── logo.png            # AI-generated application logo
│       └── logo.svg            # Original SVG logo (deprecated)
│
├── flask_api/              # API modules
│   ├── app.py
│   ├── models.py
│   ├── routes.py
│   └── utils.py
│
└── uploads/                # User-uploaded files
```

## User Preferences
*No specific preferences recorded yet*

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (optional, defaults to SQLite)
- `SESSION_SECRET`: Flask session secret key
- `STREAMLIT_URL`: External Streamlit app URL (if applicable)

## Development Notes

### Running the Application
The Flask server runs on port 5000 with auto-reload enabled for development. The workflow is configured to run `python main.py`.

### Database
- Development: SQLite (default) or PostgreSQL via `DATABASE_URL`
- Automatically creates tables on first run
- Session-based file tracking for uploads

### 3D Performance Optimization
- Three.js particle count optimized to 1500 particles
- Animations use requestAnimationFrame for smooth 60fps
- Glassmorphism effects use GPU-accelerated backdrop-filter
- Lazy loading for heavy visualizations

### Browser Compatibility
- Modern browsers with WebGL support recommended
- Fallback styling for browsers without backdrop-filter support
- Responsive design works on mobile (3D effects simplified)

## Deployment
- **Type**: Autoscale (stateless)
- **Command**: `gunicorn --bind=0.0.0.0:5000 --reuse-port main:app`
- **Port**: 5000 (only exposed port)
- **Build**: None required (Python application)

## Dependencies Highlights
- All Python dependencies in `requirements.txt`
- CDN-hosted frontend libraries (Bootstrap, Three.js, Plotly, Font Awesome)
- No npm/node dependencies required

## Known Limitations
- Large datasets (>10MB CSV) may require longer processing time
- Streamlit app currently redirects to external URL
- Three.js WebGL may not work in headless screenshot environments (works fine for users)

## Future Enhancements
- Add 3D surface plots for multi-dimensional data
- Implement real-time data streaming
- Add export functionality for all visualizations
- Integrate more ML models (RFM analysis, market basket analysis)
- Add user authentication and multi-tenancy support
