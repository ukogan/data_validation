# ODCV Automated Database Pipeline

One-click solution to query database → export CSV → generate interactive dashboard.

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)
```bash
# Setup
./setup_automation.sh

# Configure database in .env file
# Then start web server
python3 web_server.py

# Open browser to: http://localhost:5000
# Click button to execute pipeline!
```

### Option 2: Command Line
```bash
# Basic usage
python3 automated_pipeline.py your_view_name

# With time range
python3 automated_pipeline.py sensor_data_view '2025-09-16 08:00' 12
```

## 📋 Requirements

**Environment Variables:**
- `DB_HOST` - Database server hostname
- `DB_NAME` - Database name with sensor data
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `DB_PORT` - Database port (default: 5432)
- `DB_TYPE` - Database type (default: postgresql)

**Python Dependencies:**
```bash
pip3 install -r requirements_automation.txt
```

## 🏗️ Architecture

```
Database View → CSV Export → ODCV Dashboard
     ↓              ↓             ↓
   Query         Temp File    Interactive HTML
```

**Components:**
- `src/data/db_connector.py` - Database integration module
- `automated_pipeline.py` - Complete automation script
- `web_server.py` - Flask web interface
- `web_interface.html` - Button-triggered dashboard

## 📊 Database Schema Expected

Your database view should have columns matching:
```sql
CREATE VIEW sensor_data_view AS
SELECT
    timestamp_column as time,
    sensor_name_column as name,
    sensor_value_column as value
FROM your_sensor_table
WHERE ...
```

## 🔧 Configuration

### Database Types Supported
- **PostgreSQL** (default) - `psycopg2-binary` driver
- **MySQL** - `pymysql` driver
- **SQLite** - Built-in support

### Query Customization
Modify `ODCVQueryBuilder.build_sensor_query()` for:
- Custom column names
- Additional WHERE clauses
- Time zone handling
- Sensor filtering

## 🎯 Usage Examples

### Web Interface Workflow
1. Open http://localhost:5000
2. Enter database view name
3. Set time range (optional)
4. Click "Execute Pipeline"
5. Dashboard opens automatically

### Command Line Examples
```bash
# Last 24 hours from default view
python3 automated_pipeline.py bms_sensor_readings

# Specific time window
python3 automated_pipeline.py facility_data '2025-09-15 17:00' 22

# Short analysis period
python3 automated_pipeline.py zone_sensors '2025-09-16 08:00' 8
```

## 🔍 Integration with Existing ODCV System

This automation leverages your existing modular ODCV components:
- `src/data/data_loader.py` - CSV parsing
- `src/analysis/timeline_processor.py` - Data analysis
- `src/presentation/html_generator.py` - Dashboard generation

**Result:** Same interactive timeline dashboard, now automated from database!

## 🚦 Error Handling

**Common Issues:**
- Missing env vars → Clear error messages
- Database connection fails → Connection test endpoint
- Invalid time formats → Validation with examples
- Query errors → Detailed SQL error reporting

## 🧹 Cleanup

Temporary CSV files are kept for debugging. To auto-cleanup, uncomment:
```python
# In automated_pipeline.py
pipeline.cleanup()
```

## 📈 Scalability Notes

- Large datasets: Consider chunked queries for >1M records
- Multiple facilities: Add facility_id to query builder
- Real-time updates: Extend for periodic refresh
- Performance: Add query result caching for repeated analysis