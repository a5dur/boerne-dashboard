import pandas as pd
import geopandas as gpd
from datetime import datetime
import numpy as np
from pathlib import Path
from google.oauth2.service_account import Credentials
import pygsheets
from typing import Union, List, Dict
from global0_set_apis_libraries import GlobalSetup

class GroundwaterProcessor:
    """Process and analyze groundwater data for Boerne Water Dashboard."""
    
    def __init__(self):
        """Initialize with global setup configuration."""
        self.setup = GlobalSetup()
        self.logger = self.setup.logger
        
        # Paths
        self.gw_dir = self.setup.data_dir / "gw"
        self.gw_dir.mkdir(exist_ok=True)
        
        # Load initial data
        self._load_historical_data()
        
    def _load_historical_data(self):
        """Load historical groundwater data and metadata."""
        try:
            self.well_metadata = pd.read_csv(self.gw_dir / "well_metadata.csv")
            self.historic_data = pd.read_csv(self.gw_dir / "historic_gw_depth.csv")
            self.historic_data['date'] = pd.to_datetime(self.historic_data['date'])
            self.historic_data['site'] = self.historic_data['site'].astype(str)
            
            self.logger.info("Historical groundwater data loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
            raise
            
    def _fetch_gsheet_data(self) -> pd.DataFrame:
        """Fetch new groundwater data from Google Sheets."""
        try:
            gc = pygsheets.authorize(service_account_env_var='GSHEET_SERVICE_ACCOUNT')
            sheet_id = "1QoaOhrpz6vrSMBc0yc5-i7nhwj2lmsBHZFYOBJc0KVU"
            sheet = gc.open_by_key(sheet_id)
            
            all_well_metadata = pd.DataFrame()
            all_well_data = pd.DataFrame()
            
            # Process each sheet (1-42)
            for sheet_num in range(1, 43):
                # Get metadata
                metadata = sheet[sheet_num-1].get_values('A2:X3', value_render='UNFORMATTED_VALUE')
                metadata_df = pd.DataFrame(metadata[1:], columns=metadata[0])
                metadata_df['Long_Va'] = metadata_df.iloc[0, 1]
                metadata_df['Lat_Va'] = metadata_df.iloc[0, 2]
                
                # Get well data
                data = sheet[sheet_num-1].get_values('A6:C', value_render='UNFORMATTED_VALUE')
                data_df = pd.DataFrame(data[1:], columns=['date', 'depth_ft', 'elevation'])
                data_df['State_Number'] = metadata_df.iloc[0, 14]
                
                all_well_metadata = pd.concat([all_well_metadata, metadata_df])
                all_well_data = pd.concat([all_well_data, data_df])
                
                self.logger.info(f"Completed sheet {sheet_num} ({sheet_num/42*100:.1f}% complete)")
                
            return all_well_metadata, all_well_data
            
        except Exception as e:
            self.logger.error(f"Error fetching Google Sheets data: {e}")
            raise
            
    def process_groundwater_data(self, well_data: pd.DataFrame) -> pd.DataFrame:
        """Process groundwater data with proper formatting and julian dates."""
        try:
            df = well_data.copy()
            
            # Rename columns
            df = df.rename(columns={
                'State_Number': 'site',
                'elevation': 'elevation_at_waterlevel'
            })
            
            # Convert types
            df['site'] = df['site'].astype(str)
            df['date'] = pd.to_datetime(df['date'])
            df['depth_ft'] = pd.to_numeric(df['depth_ft'], errors='coerce')
            
            # Add julian dates using global setup
            df['year'] = df['date'].dt.year
            df['day_month'] = df['date'].dt.strftime('%m-%d')
            
            df = self.setup.add_julian_dates(df)
            
            # Add agency
            df['agency'] = 'CCGCD'
            
            # Remove missing data
            df = df.dropna()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error processing groundwater data: {e}")
            raise
            
    def calculate_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate groundwater statistics by site and julian day."""
        try:
            stats = []
            
            for site in df['site'].unique():
                site_data = df[df['site'] == site]
                
                # Calculate stats by julian day
                site_stats = (site_data.groupby(['site', 'julian'])
                            .agg({
                                'depth_ft': [
                                    'count',
                                    'min',
                                    lambda x: np.percentile(x, 10),
                                    lambda x: np.percentile(x, 25),
                                    lambda x: np.percentile(x, 50),
                                    lambda x: np.percentile(x, 75),
                                    lambda x: np.percentile(x, 90),
                                    'max'
                                ]
                            }).reset_index())
                
                stats.append(site_stats)
                
            stats_df = pd.concat(stats)
            
            # Rename columns
            stats_df.columns = [
                'site', 'julian', 'Nobs', 'min', 'flow10', 'flow25',
                'flow50', 'flow75', 'flow90', 'max'
            ]
            
            return stats_df
            
        except Exception as e:
            self.logger.error(f"Error calculating statistics: {e}")
            raise
            
    def determine_status(self, current: float, stats: pd.Series) -> str:
        """Determine groundwater status based on percentiles."""
        if pd.isna(current):
            return "unknown"
        elif current <= stats['flow10']:
            return "Extremely Wet"
        elif current <= stats['flow25']:
            return "Very Wet"
        elif current < stats['flow50']:
            return "Moderately Wet"
        elif current < stats['flow75']:
            return "Moderately Dry"
        elif current < stats['flow90']:
            return "Very Dry"
        else:
            return "Extremely Dry"
            
    def create_geojson(self, df: pd.DataFrame, stats: pd.DataFrame) -> gpd.GeoDataFrame:
        """Create GeoJSON with current conditions."""
        try:
            # Merge current conditions with stats
            current_conditions = df.merge(
                stats,
                on=['site', 'julian'],
                how='left'
            )
            
            # Add status
            current_conditions['status'] = current_conditions.apply(
                lambda row: self.determine_status(row['depth_ft'], row),
                axis=1
            )
            
            # Create GeoDataFrame
            gdf = gpd.GeoDataFrame(
                current_conditions,
                geometry=gpd.points_from_xy(
                    self.well_metadata['dec_long_va'],
                    self.well_metadata['dec_lat_va']
                ),
                crs="EPSG:4326"
            )
            
            return gdf
            
        except Exception as e:
            self.logger.error(f"Error creating GeoJSON: {e}")
            raise
            
    def save_outputs(self, df: pd.DataFrame, stats: pd.DataFrame, gdf: gpd.GeoDataFrame):
        """Save all processed data files."""
        try:
            # Save main depth data
            df.to_csv(self.gw_dir / "all_gw_depth.csv", index=False)
            
            # Save monthly averages
            monthly_avg = (df.groupby(['site', pd.Grouper(key='date', freq='M')])
                         .agg({'depth_ft': 'mean'})
                         .reset_index())
            monthly_avg.to_csv(self.gw_dir / "all_monthly_avg.csv", index=False)
            
            # Save statistics
            stats.to_csv(self.gw_dir / "all_gw_stats.csv", index=False)
            
            # Save GeoJSON
            gdf.to_file(self.gw_dir / "all_gw_sites.geojson", driver='GeoJSON')
            
            self.logger.info("All groundwater data files saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving output files: {e}")
            raise
            
    def update_groundwater_data(self):
        """Main method to update all groundwater-related data."""
        try:
            # Fetch new data
            well_metadata, well_data = self._fetch_gsheet_data()
            
            # Process new data
            processed_data = self.process_groundwater_data(well_data)
            
            # Calculate statistics
            stats = self.calculate_statistics(processed_data)
            
            # Create GeoJSON with current conditions
            geojson = self.create_geojson(processed_data, stats)
            
            # Save all outputs
            self.save_outputs(processed_data, stats, geojson)
            
            self.logger.info("Groundwater data update completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in groundwater update process: {e}")
            raise

if __name__ == "__main__":
    processor = GroundwaterProcessor()
    processor.update_groundwater_data()