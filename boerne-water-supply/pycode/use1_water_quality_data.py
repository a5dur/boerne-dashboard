import pandas as pd
import geopandas as gpd
from pathlib import Path
import pygsheets
from datetime import datetime
from typing import List, Dict
from global0_set_apis_libraries import GlobalSetup

class WaterQualityProcessor:
    """Process water quality monitoring data for Boerne Water Dashboard.
    
    Originally created by Vianey Rueda (March 2022)
    Converted to Python and enhanced for the current system.
    """
    
    def __init__(self):
        """Initialize with global setup configuration."""
        self.setup = GlobalSetup()
        self.logger = self.setup.logger
        
        # Initialize paths
        self.quality_dir = self.setup.data_dir / "quality"
        self.quality_dir.mkdir(exist_ok=True)
        
        # Monitoring site IDs
        self.monitored_sites = [
            "12600", "15126", "20823", "80186", "80230", 
            "80904", "80966", "81596", "81641", "81671", "81672"
        ]
        
        # Column mappings for data cleanup
        self.column_mappings = {
            'Name': 'site_id',
            'Description': 'name',
            'Basin': 'basin',
            'County': 'county',
            'Latitude': 'latitude',
            'Longitude': 'longitude',
            'TCEQ Stream Segment': 'stream_segment',
            'Sample Date': 'date',
            'Sample Depth (m)': 'sample_depth',
            'Flow Severity': 'flow_severity',
            'Conductivity (µs/cm)': 'conductivity',
            'Dissolved Oxygent (mg/L)': 'dissolved_oxygen',
            'Air Temperature (°C)': 'air_temp',
            'Water Temperature (°C)': 'water_temp',
            'E. Coli Average': 'ecoli_avg',
            'Secchi Disk Transparency (m)': 'secchi_disk_transparency',
            'Nitrate-Nitrogen (ppm or mg/L)': 'nitrate_nitrogen'
        }
        
        self._load_historical_data()
        
    def _load_historical_data(self):
        """Load historical water quality data and monitoring sites."""
        try:
            # Load historical data
            self.historic_data = pd.read_csv(
                self.quality_dir / "historic_water_quality.csv"
            )
            
            # Load monitoring sites
            self.monitoring_sites = gpd.read_file(
                self.quality_dir / "water_quality_sites.geojson"
            )
            
            self.logger.info("Historical water quality data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
            raise
            
    def _fetch_gsheet_data(self) -> pd.DataFrame:
        """Fetch new water quality data from Google Sheets."""
        try:
            # Initialize Google Sheets client
            gc = pygsheets.authorize(service_account_env_var='GSHEET_SERVICE_ACCOUNT')
            
            # Open spreadsheet and get data
            spreadsheet_id = "1JAQLzSpbU2nMVb4Pe1XUA2lxU3a1XcY4oUYS8UhIaiA"
            sheet = gc.open_by_key(spreadsheet_id)
            worksheet = sheet[0]
            
            # Get data and convert to DataFrame
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Filter for monitored sites
            df = df[df['Name'].isin(self.monitored_sites)]
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching Google Sheets data: {e}")
            raise
            
    def _process_quality_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process and clean water quality data."""
        try:
            # Rename columns
            df = df.rename(columns=self.column_mappings)
            
            # Convert date column
            df['date'] = pd.to_datetime(df['date'])
            
            # Add year column
            df['year'] = df['date'].dt.year
            
            # Sort data
            df = df.sort_values(['site_id', 'date'])
            
            # Remove unnecessary columns
            columns_to_keep = [
                'site_id', 'name', 'basin', 'county', 'latitude', 
                'longitude', 'stream_segment', 'date', 'sample_depth',
                'flow_severity', 'conductivity', 'dissolved_oxygen',
                'air_temp', 'water_temp', 'ecoli_avg',
                'secchi_disk_transparency', 'nitrate_nitrogen', 'year'
            ]
            df = df[columns_to_keep]
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error processing quality data: {e}")
            raise
            
    def update_water_quality_data(self):
        """Main method to update water quality data."""
        try:
            # Fetch new data
            new_data = self._fetch_gsheet_data()
            
            # Process new data
            processed_data = self._process_quality_data(new_data)
            
            # Filter for recent data (2022 onwards)
            new_data = processed_data[
                processed_data['year'] >= 2022
            ].copy()
            
            # Combine with historical data
            combined_data = pd.concat(
                [self.historic_data, new_data],
                ignore_index=True
            )
            
            # Save updated data
            self._save_processed_data(combined_data)
            
            self.logger.info("Water quality data update completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating water quality data: {e}")
            raise
            
    def _save_processed_data(self, df: pd.DataFrame):
        """Save processed water quality data."""
        try:
            output_path = self.quality_dir / "all_water_quality.csv"
            df.to_csv(output_path, index=False)
            
            self.logger.info(f"Water quality data saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving processed data: {e}")
            raise

if __name__ == "__main__":
    processor = WaterQualityProcessor()
    processor.update_water_quality_data()
