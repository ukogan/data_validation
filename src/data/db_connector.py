"""
Database connection module for ODCV analytics dashboard.
Handles database queries and CSV export functionality.
"""

import os
import csv
import tempfile
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd

# Database connectors (install as needed)
try:
    import psycopg2  # PostgreSQL
    import psycopg2.extras
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

try:
    import sqlalchemy  # Generic SQL
    from sqlalchemy import create_engine, text
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False


class DatabaseConnector:
    """Generic database connector for ODCV sensor data queries"""

    def __init__(self, connection_string: str, db_type: str = "postgresql"):
        """
        Initialize database connector

        Args:
            connection_string: Database connection string
            db_type: Database type (postgresql, mysql, sqlite, etc.)
        """
        self.connection_string = connection_string
        self.db_type = db_type
        self.engine = None

        if HAS_SQLALCHEMY:
            self.engine = create_engine(connection_string)

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if self.engine:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return True
            return False
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    def execute_query(self, query: str, params: Dict = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            pandas DataFrame with results
        """
        if not self.engine:
            raise Exception("Database engine not available. Install sqlalchemy and database driver.")

        try:
            with self.engine.connect() as conn:
                if params:
                    result = pd.read_sql_query(text(query), conn, params=params)
                else:
                    result = pd.read_sql_query(text(query), conn)
                return result
        except Exception as e:
            print(f"Query execution failed: {e}")
            raise

    def query_to_csv(self, query: str, output_path: str, params: Dict = None) -> str:
        """
        Execute query and save results to CSV

        Args:
            query: SQL query string
            output_path: Path for output CSV file
            params: Query parameters

        Returns:
            Path to created CSV file
        """
        df = self.execute_query(query, params)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

        # Transform data to match timeline_visualizer expected format
        # Your query returns: point_id, name, parent_name, time, insert_time, value
        # timeline_visualizer expects: time, name, value

        if 'time' in df.columns and 'name' in df.columns and 'value' in df.columns:
            # Use your exact column names
            output_df = df[['time', 'name', 'value']].copy()
        else:
            # Fallback to all columns
            output_df = df.copy()

        # Save to CSV with proper formatting for timeline_visualizer
        output_df.to_csv(output_path, index=False)

        print(f"Query results saved to: {output_path}")
        print(f"Records exported: {len(df)}")

        return output_path


class ODCVQueryBuilder:
    """Helper class for building ODCV-specific sensor queries"""

    @staticmethod
    def build_sensor_query(
        view_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        sensor_names: Optional[List[str]] = None,
        time_column: str = "time",
        name_column: str = "name",
        value_column: str = "value"
    ) -> str:
        """
        Build standardized sensor data query for ODCV dashboard

        Args:
            view_name: Database view/table name
            start_time: Filter start time
            end_time: Filter end time
            sensor_names: List of specific sensors to include
            time_column: Name of timestamp column
            name_column: Name of sensor name column
            value_column: Name of sensor value column

        Returns:
            SQL query string
        """
        query = f"""
        SELECT
            {time_column} as time,
            {name_column} as name,
            {value_column} as value
        FROM {view_name}
        WHERE 1=1
        """

        if start_time:
            query += f"\n    AND {time_column} >= :start_time"

        if end_time:
            query += f"\n    AND {time_column} <= :end_time"

        if sensor_names:
            placeholders = ', '.join([f"':sensor_{i}'" for i in range(len(sensor_names))])
            query += f"\n    AND {name_column} IN ({placeholders})"

        query += f"\nORDER BY {time_column}, {name_column}"

        return query

    @staticmethod
    def get_common_sensor_patterns() -> Dict[str, str]:
        """Return common sensor name patterns for ODCV systems"""
        return {
            "occupancy_sensors": "name LIKE '%presence%' OR name LIKE '%occupancy%'",
            "zone_modes": "name LIKE '%mode%' OR name LIKE 'BV%'",
            "temperature": "name LIKE '%temp%' OR name LIKE '%temperature%'",
            "damper_position": "name LIKE '%damper%' OR name LIKE '%position%'"
        }


def create_connection_from_env() -> Optional[DatabaseConnector]:
    """Create database connection from environment variables"""

    # Try to get connection details from environment
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_type = os.getenv('DB_TYPE', 'postgresql')

    if not all([db_host, db_name, db_user, db_password]):
        print("Missing database environment variables:")
        print("Required: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
        print("Optional: DB_PORT (default: 5432), DB_TYPE (default: postgresql)")
        return None

    if db_type == 'postgresql':
        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_type == 'mysql':
        connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_type == 'sqlite':
        connection_string = f"sqlite:///{db_name}"
    else:
        print(f"Unsupported database type: {db_type}")
        return None

    return DatabaseConnector(connection_string, db_type)


# Example usage and testing
if __name__ == "__main__":
    # Test connection
    db = create_connection_from_env()
    if db and db.test_connection():
        print("Database connection successful!")

        # Example query
        query = ODCVQueryBuilder.build_sensor_query(
            "sensor_data_view",
            start_time=datetime(2025, 9, 15, 17, 0),
            end_time=datetime(2025, 9, 16, 15, 0)
        )

        print("Generated query:")
        print(query)
    else:
        print("Database connection failed or not configured")