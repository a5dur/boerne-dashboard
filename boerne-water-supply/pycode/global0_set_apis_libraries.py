import os
import sys
import pandas as pd
import numpy as np
import datetime
from datetime import date
import geopandas as gpd
from pathlib import Path
import json
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import logging
from typing import List, Union
import warnings

class GlobalSetup:
    """Initialize global settings and utilities for Boerne Water Dashboard."""
    
    def __init__(self):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Disable scientific notation
        pd.set_option('display.float_format', lambda x: '%.5f' % x)
        
        # Set working directory and paths
        self.setup_paths()
        
        # State information
        self.state_abb = "TX"
        self.state_fips = 48
        
        # Date settings
        self.setup_dates()
        
        # Create update date file
        self.create_update_date()
        
        # Create julian calendar reference
        self.julian_ref = self.create_julian_reference()
        # In global0_set_apis_libraries.py
        print(f"Julian calendar file location: {self.data_dir / 'julian-daymonth.csv'}")
        print("Does file exist?", (self.data_dir / 'julian-daymonth.csv').exists())
        
        # Required packages - equivalent to R libraries
        self.required_packages = [
            "pandas", "geopandas", "requests", "numpy", "google-auth",
            "google-auth-oauthlib", "google-api-python-client",
            "shapely", "pyproj", "rasterio", "folium", "beautifulsoup4",
            "noaa-sdk", "hydrodata"  # Python equivalents for R packages
        ]
        
        # Install required packages
        self.install_required_packages()

    def setup_paths(self):
        """Set up working directory and data paths."""
        try:
            self.source_path = os.getcwd()
            self.data_dir = Path("boerne-water-supply/data/")
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Working directory: {self.source_path}")
            self.logger.info(f"Data directory: {self.data_dir}")
        except Exception as e:
            self.logger.error(f"Error setting up paths: {e}")
            raise

    def setup_dates(self):
        """Initialize date-related variables."""
        self.today = date.today()
        self.current_year = self.today.year
        self.start_date = "1990-01-01"
        self.end_date = f"{self.current_year}-12-31"
        self.months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def create_update_date(self):
        """Create update date CSV file."""
        try:
            update_date = pd.DataFrame({
                "today_date": [f"{self.months[self.today.month - 1]} "
                             f"{self.today.day}, {self.today.year}"]
            })
            update_date.to_csv(self.data_dir / "update_date.csv", index=False)
            self.logger.info("Update date file created successfully")
        except Exception as e:
            self.logger.error(f"Error creating update date file: {e}")
            raise

    @staticmethod
    def moving_average(data: Union[List, np.ndarray], window: int = 7) -> np.ndarray:
        """Calculate moving average with specified window size."""
        return pd.Series(data).rolling(window=window, min_periods=1).mean().to_numpy()

    @staticmethod
    def notin(x: list, y: list) -> list:
        """Python equivalent of R's %notin% function."""
        return [item for item in x if item not in y]
    
    

    def create_julian_reference(self) -> pd.DataFrame:
        """Create standardized julian date reference."""
        try:
            # Create date range for non-leap year
            jan1 = datetime.date(2021, 1, 1)
            dec31 = datetime.date(2021, 12, 31)
            all_dates = pd.date_range(jan1, dec31)
            
            # Create initial DataFrame for non-leap year
            julian_df = pd.DataFrame({
                'day_month': all_dates.strftime('%m-%d'),
                'julian_index': range(1, len(all_dates) + 1)
            })
            
            # Create leap year data
            leap_dates = pd.date_range(
                datetime.date(2020, 1, 1),  # 2020 was a leap year
                datetime.date(2020, 12, 31)
            )
            leap_day_month = leap_dates.strftime('%m-%d')
            
            # Add leap year columns
            julian_df['day_month_leap'] = julian_df['day_month'].copy()
            julian_df['julian_index_leap'] = julian_df['julian_index'].copy()
            
            # Insert Feb 29 for leap year
            feb29_entry = pd.DataFrame({
                'day_month': ['02-29'],
                'julian_index': [np.nan],
                'day_month_leap': ['02-29'],
                'julian_index_leap': [60]
            })
            
            # Concatenate properly
            julian_df = pd.concat([
                julian_df.iloc[:59],
                feb29_entry,
                julian_df.iloc[59:]
            ]).reset_index(drop=True)
            
            # Adjust julian_index_leap after Feb 29
            julian_df.loc[60:, 'julian_index_leap'] = range(61, 367)

            
            self.logger.info("Julian reference created successfully")

            return julian_df

        
            
        except Exception as e:
            self.logger.error(f"Error creating julian reference: {e}")
            raise

    def install_required_packages(self):
        """Check and install required packages."""
        for package in self.required_packages:
            try:
                __import__(package.replace("-", "_"))
                self.logger.info(f"Package {package} is already installed")
            except ImportError:
                self.logger.warning(f"Installing {package}...")
                os.system(f"{sys.executable} -m pip install {package}")

if __name__ == "__main__":
    setup = GlobalSetup()
    print("Global setup completed successfully")
