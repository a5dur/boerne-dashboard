import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import requests
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple
from global0_set_apis_libraries import GlobalSetup

class StreamflowProcessor:
    """Process and analyze USGS streamflow data for Boerne Water Dashboard."""
    
    def __init__(self):
        """Initialize with global setup and configuration."""
        self.setup = GlobalSetup()
        self.logger = self.setup.logger
        
        # USGS configurations
        self.parameter_code = '00060'  # discharge in cubic feet per second
        self.statistic_code = '00003'  # mean
        self.service = 'dv'  # daily values
        
        # Initialize paths
        self.streamflow_dir = self.setup.data_dir / "streamflow"
        self.streamflow_dir.mkdir(exist_ok=True)
        
        # Load initial data
        self._load_historical_data()
        
    def _load_historical_data(self):
        """Load historical streamflow data and site information."""
        try:
            # Load site information
            self.sites = gpd.read_file(
                self.streamflow_dir / "stream_gauge_sites.geojson"
            )[['site', 'name', 'huc8', 'startYr', 'endYr', 
               'nYears', 'geometry', 'ws_watershed']]
            
            # Load site metadata
            self.site_metadata = pd.read_csv(
                self.streamflow_dir / "stream_gauge_metadata.csv"
            )
            
            # Load historical flow data
            self.historic_data = pd.read_csv(
                self.streamflow_dir / "historic_stream_data.csv",
                dtype={'site': str}
            )
            self.historic_data['date'] = pd.to_datetime(
                self.historic_data['date']
            )
            
            self.logger.info("Historical data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
            raise
            
    def _fetch_nwis_data(self, site: str, start_date: str, 
                        end_date: str) -> pd.DataFrame:
        """Fetch data from USGS NWIS web service."""
        try:
            url = (
                f"https://waterservices.usgs.gov/nwis/dv/"
                f"?format=json&sites={site}"
                f"&startDT={start_date}&endDT={end_date}"
                f"&parameterCd={self.parameter_code}"
                f"&statCd={self.statistic_code}"
            )
            
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Extract time series data
            if 'value' in data['value']['timeSeries'][0]:
                values = data['value']['timeSeries'][0]['values'][0]['value']
                df = pd.DataFrame(values)
                df['site'] = site
                df['datetime'] = pd.to_datetime(df['dateTime'])
                df['value'] = pd.to_numeric(df['value'])
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error fetching NWIS data for site {site}: {e}")
            raise
            
    def _calculate_rolling_average(self, df: pd.DataFrame, 
                                 window: int = 7) -> pd.DataFrame:
        """Calculate rolling average using global setup's moving average."""
        try:
            df = df.copy()
            df['roll_mean'] = df.groupby('site')['value'].transform(
                lambda x: self.setup.moving_average(x, window)
            )
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating rolling average: {e}")
            raise
            
    def _calculate_flow_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate flow statistics by site and julian day."""
        try:
            stats = []
            
            for site in df['site'].unique():
                site_data = df[df['site'] == site]
                
                site_stats = site_data.groupby(['site', 'julian']).agg({
                    'roll_mean': [
                        'count',
                        'min',
                        lambda x: np.percentile(x, 10),
                        lambda x: np.percentile(x, 25),
                        lambda x: np.percentile(x, 50),
                        lambda x: np.percentile(x, 75),
                        lambda x: np.percentile(x, 90),
                        'max'
                    ]
                }).reset_index()
                
                site_stats.columns = [
                    'site', 'julian', 'Nobs', 'min', 'flow10',
                    'flow25', 'flow50', 'flow75', 'flow90', 'max'
                ]
                
                # Add year information
                site_stats['startYr'] = site_data['year'].min()
                site_stats['endYr'] = site_data['year'].max()
                
                stats.append(site_stats)
            
            return pd.concat(stats, ignore_index=True)
            
        except Exception as e:
            self.logger.error(f"Error calculating flow statistics: {e}")
            raise

    def determine_status(self, row: pd.Series) -> str:
        """Determine streamflow status based on percentiles."""
        if pd.isna(row['flow']):
            return "unknown"
        elif row['flow'] <= row['flow10']:
            return "Extremely Dry"
        elif row['flow'] <= row['flow25']:
            return "Very Dry"
        elif row['flow'] < row['flow50']:
            return "Moderately Dry"
        elif row['flow'] < row['flow75']:
            return "Moderately Wet"
        elif row['flow'] < row['flow90']:
            return "Very Wet"
        else:
            return "Extremely Wet"

    def get_status_color(self, status: str) -> str:
        """Get color code for flow status."""
        color_map = {
            "Extremely Dry": "darkred",
            "Very Dry": "red",
            "Moderately Dry": "orange",
            "Moderately Wet": "cornflowerblue",
            "Very Wet": "blue",
            "Extremely Wet": "navy",
            "unknown": "gray"
        }
        return color_map.get(status, "gray")

    def update_streamflow_data(self):
        """Main method to update all streamflow-related data."""
        try:
            # Get latest data for each site
            new_data = []
            for site in self.sites['site'].unique():
                last_date = self.historic_data[
                    self.historic_data['site'] == site
                ]['date'].max()
                
                site_data = self._fetch_nwis_data(
                    site,
                    (last_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                    self.setup.today.strftime('%Y-%m-%d')
                )
                
                if not site_data.empty:
                    new_data.append(site_data)
            
            if new_data:
                new_data = pd.concat(new_data, ignore_index=True)
                
                # Process new data
                new_data['julian'] = new_data['datetime'].dt.dayofyear
                new_data['year'] = new_data['datetime'].dt.year
                new_data = self._calculate_rolling_average(new_data)
                
                # Combine with historical data
                combined_data = pd.concat(
                    [self.historic_data, new_data], 
                    ignore_index=True
                )
                
                # Calculate statistics
                stats = self._calculate_flow_statistics(combined_data)
                
                # Calculate current conditions
                current_conditions = self._calculate_current_conditions(
                    combined_data,
                    stats
                )
                
                # Save results
                self._save_processed_data(
                    combined_data,
                    stats,
                    current_conditions
                )
                
            self.logger.info("Streamflow data update completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating streamflow data: {e}")
            raise

    def _calculate_current_conditions(
        self, 
        data: pd.DataFrame, 
        stats: pd.DataFrame
    ) -> pd.DataFrame:
        """Calculate current conditions for each site."""
        try:
            # Get most recent data for each site
            current = data.loc[data.groupby('site')['datetime'].idxmax()]
            
            # Merge with statistics
            conditions = current.merge(
                stats,
                on=['site', 'julian'],
                how='left'
            )
            
            # Determine status
            conditions['status'] = conditions.apply(
                self.determine_status,
                axis=1
            )
            conditions['color'] = conditions['status'].map(
                self.get_status_color
            )
            
            return conditions
            
        except Exception as e:
            self.logger.error(f"Error calculating current conditions: {e}")
            raise

    def _save_processed_data(
        self, 
        data: pd.DataFrame,
        stats: pd.DataFrame,
        current: pd.DataFrame
    ):
        """Save all processed streamflow data."""
        try:
            # Save main streamflow data
            data.to_csv(
                self.streamflow_dir / "all_stream_data.csv",
                index=False
            )
            
            # Save statistics
            stats.to_csv(
                self.streamflow_dir / "all_stream_stats.csv",
                index=False
            )
            
            # Update sites GeoJSON with current conditions
            sites_with_conditions = self.sites.merge(
                current[['site', 'status', 'flow', 'flow50']],
                on='site',
                how='left'
            )
            sites_with_conditions.to_file(
                self.streamflow_dir / "all_stream_gauge_sites.geojson",
                driver='GeoJSON'
            )
            
            # Save current status by watershed
            current_status = current.merge(
                self.sites[['site', 'huc8', 'ws_watershed']],
                on='site',
                how='left'
            )
            current_status.to_csv(
                self.streamflow_dir / "current_sites_status.csv",
                index=False
            )
            
            self.logger.info("All streamflow data files saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving processed data: {e}")
            raise

if __name__ == "__main__":
    processor = StreamflowProcessor()
    processor.update_streamflow_data()