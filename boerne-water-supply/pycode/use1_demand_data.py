from global0_set_apis_libraries import GlobalSetup
import pandas as pd
import geopandas as gpd
from datetime import datetime
import numpy as np
from pathlib import Path
from google.oauth2.service_account import Credentials
import pygsheets
from typing import Union, List, Dict

class DemandDataProcessor:
    """Process and analyze water demand data for Boerne Water Dashboard."""
    
    def __init__(self):
        """Initialize with global setup configuration."""
        # Initialize global setup
        self.setup = GlobalSetup()
        self.logger = self.setup.logger
        
        # Use paths from global setup
        self.data_dir = self.setup.data_dir
        self.demand_dir = self.data_dir / "demand"
        self.demand_dir.mkdir(exist_ok=True)
        
        # Use state info from global setup
        self.state_abb = self.setup.state_abb
        self.state_fips = self.setup.state_fips
        
        # Use date settings from global setup
        self.today = self.setup.today
        self.current_year = self.setup.current_year
        self.start_date = self.setup.start_date
        self.end_date = self.setup.end_date
        self.months = self.setup.months
        
        # Load utilities data
        self._load_utility_data()
        self._load_historical_data()
        
    def _load_utility_data(self):
        """Load utility geojson data."""
        try:
            self.utilities = gpd.read_file(self.data_dir / "utility.geojson")
            self.pwsid_list = self.utilities['pwsid'].unique()
            self.logger.info("Utility data loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading utility data: {e}")
            raise

    def _load_historical_data(self):
        """Load historical demand data using global setup paths."""
        try:
            self.old_total_demand = pd.read_csv(
                self.demand_dir / "historic_total_demand.csv")
            self.old_demand_by_source = pd.read_csv(
                self.demand_dir / "historic_demand_by_source.csv")
            self.old_reclaimed = pd.read_csv(
                self.demand_dir / "historic_reclaimed_water.csv")
            self.old_pop = pd.read_csv(
                self.demand_dir / "historic_pop.csv")
            self.logger.info("Historical data loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
            raise

    def process_demand_by_source(self, demand_data: pd.DataFrame) -> pd.DataFrame:
        """Process demand data by source using global setup utilities."""
        try:
            # Use global setup's moving average function for smoothing
            df = demand_data.copy()
            
            # Convert values to MGD
            mgd_columns = ['groundwater', 'boerne_lake', 'GBRA', 'reclaimed', 'total']
            df[mgd_columns] = df[mgd_columns].apply(pd.to_numeric, errors='coerce').fillna(0) / 1000
            
            # Calculate moving averages using global setup's function
            for col in mgd_columns:
                df[f'{col}_ma'] = self.setup.moving_average(df[col].values)
            
            # Add julian dates using global setup's calendar
            df = self.add_julian_dates(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error processing demand by source: {e}")
            raise

    def add_julian_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add julian dates using global setup's julian calendar."""
        try:
            df['date'] = pd.to_datetime(df['date'])
            df['year'] = df['date'].dt.year
            df['day_month'] = df['date'].dt.strftime('%m-%d')
            
            # Use global setup's julian reference
            julian_ref = self.setup.julian_ref
            
            def get_julian_day(row):
                is_leap = pd.Timestamp(row['date']).is_leap_year
                day_month_col = 'day_month_leap' if is_leap else 'day_month'
                julian_col = 'julian_index_leap' if is_leap else 'julian_index'
                
                return julian_ref.loc[
                    julian_ref[day_month_col] == row['day_month'], 
                    julian_col
                ].iloc[0]
            
            df['julian'] = df.apply(get_julian_day, axis=1)
            return df
            
        except Exception as e:
            self.logger.error(f"Error adding julian dates: {e}")
            raise

    def filter_new_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter new data using global setup's date settings."""
        try:
            return df[
                (df['year'] >= 2022) & 
                (df['date'] < self.today)
            ].copy()
        except Exception as e:
            self.logger.error(f"Error filtering new data: {e}")
            raise

    def calculate_demand_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate demand statistics using global setup's utilities."""
        try:
            # Use global setup's moving average function
            df['mean_demand'] = self.setup.moving_average(df['total'].values)
            
            # Calculate monthly peaks
            df['peak_demand'] = df.groupby(['pwsid', 'year', 'month'])['total'].transform(
                lambda x: x.quantile(0.98))
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating statistics: {e}")
            raise

    def calculate_cumulative_demand(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate cumulative demand using global setup's date handling."""
        try:
            df_cum = df.copy()
            df_cum['cum_demand'] = df_cum.groupby(['pwsid', 'year'])['total'].cumsum()
            return df_cum
        except Exception as e:
            self.logger.error(f"Error calculating cumulative demand: {e}")
            raise

    def save_processed_data(self, df: pd.DataFrame):
        """Save processed data using global setup's paths."""
        try:
            output_files = {
                "all_demand_by_source.csv": df,
                "all_total_demand.csv": df[['pwsid', 'date', 'total', 'mean_demand', 
                                          'julian', 'month', 'year', 'peak_demand']],
                "all_demand_cum.csv": self.calculate_cumulative_demand(df)
            }
            
            for filename, data in output_files.items():
                data.to_csv(self.demand_dir / filename, index=False)
                self.logger.info(f"Saved {filename} successfully")
                
        except Exception as e:
            self.logger.error(f"Error saving processed data: {e}")
            raise

if __name__ == "__main__":
    processor = DemandDataProcessor()
    processor.update_demand_data()