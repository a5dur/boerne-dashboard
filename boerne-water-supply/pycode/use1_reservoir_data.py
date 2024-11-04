from global0_set_apis_libraries import GlobalSetup
import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import requests
import json
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Optional
import logging



class ReservoirDataProcessor:
    """Process and analyze USACE reservoir data for Boerne Water Dashboard."""
    
    def __init__(self):
        """Initialize with global setup configuration."""
        self.setup = GlobalSetup()
        self.logger = self.setup.logger
        
        # Initialize paths - using absolute path
        self.base_path = Path("C:/Users/Admin/Documents/GitHub/boerne-dashboard-main/boerne-water-supply")
        self.reservoir_dir = self.base_path / "data/reservoirs"
        
        # Verify path exists
        if not self.reservoir_dir.exists():
            self.logger.error(f"Directory not found: {self.reservoir_dir}")
            raise FileNotFoundError(f"Directory not found: {self.reservoir_dir}")
            
        self.logger.info(f"Using reservoir directory: {self.reservoir_dir}")
        
        # USACE API configuration
        self.base_url = 'https://water.usace.army.mil/a2w/'
        self.report_url = "CWMS_CRREL.cwms_data_api.get_report_json?p_location_id="
        
        # Texas districts
        self.tx_districts = ['SWF', 'SWT', 'SWG']
        
        # Load initial data
        self._load_historical_data()
        
    def _load_historical_data(self):
        """Load historical reservoir data and site information."""
        try:
            # Load existing data with explicit paths
            usace_dams_path = self.reservoir_dir / "usace_dams.csv"
            usace_sites_path = self.reservoir_dir / "usace_sites.geojson"
            
            self.logger.info(f"Loading data from: {usace_dams_path}")
            
            # Verify files exist
            if not usace_dams_path.exists():
                self.logger.error(f"File not found: {usace_dams_path}")
                raise FileNotFoundError(f"File not found: {usace_dams_path}")
                
            if not usace_sites_path.exists():
                self.logger.error(f"File not found: {usace_sites_path}")
                raise FileNotFoundError(f"File not found: {usace_sites_path}")
            
            # Load data
            self.old_data = pd.read_csv(usace_dams_path)
            self.old_data['date'] = pd.to_datetime(self.old_data['date'])
            
            # Load site information
            self.sites = gpd.read_file(usace_sites_path)
            
            # Add URL links to sites
            res_url = "http://water.usace.army.mil/a2w/f?p=100:1:0::::P1_LINK:"
            self.sites['url_link'] = self.sites['Loc_ID'].apply(
                lambda x: f"{res_url}{x}-CWMS"
            )
            
            self.logger.info("Historical data and site information loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
            raise
    def _build_api_url(self, location_id: str) -> str:
        """Build USACE API URL for data retrieval."""
        time_amt = 2  # number of weeks
        time_unit = 'weeks'
        parameter_url = (
            f"&p_parameter_type=Stor%3AElev&p_last={time_amt}"
            f"&p_last_unit={time_unit}&p_unit_system=EN&p_format=JSON"
        )
        return f"{self.base_url}{self.report_url}{location_id}{parameter_url}"

    def _fetch_reservoir_data(self, location_id: str) -> Dict:
        """Fetch data from USACE API for a specific location."""
        try:
            url = self._build_api_url(location_id)
            
            # Add headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Make request with verification disabled
            response = requests.get(
                url, 
                headers=headers,
                timeout=15000, 
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Debug logging
            self.logger.debug(f"Raw API response for location {location_id}: {str(data)[:200]}")
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching data for location {location_id}: {e}")
            raise

    def _validate_api_response(self, data: Dict, location_id: str) -> bool:
        """Validate API response structure."""
        try:
            if not isinstance(data, dict):
                self.logger.error(f"Invalid response type for {location_id}: {type(data)}")
                return False
                
            if 'value' not in data:
                self.logger.error(f"No 'value' key in response for {location_id}")
                return False
                
            if 'timeSeries' not in data['value']:
                self.logger.error(f"No 'timeSeries' in response for {location_id}")
                return False
                
            time_series = data['value']['timeSeries']
            if not isinstance(time_series, list) or not time_series:
                self.logger.error(f"Invalid timeSeries for {location_id}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating API response: {e}")
            return False
        
    def _process_elevation_data(self, data: Dict) -> pd.DataFrame:
        """Process elevation data from API response."""
        try:
            elev_data = pd.DataFrame(data['Elev'][0])
            elev_data['date'] = pd.to_datetime(
                elev_data['time'].str[:11], 
                format='%d-%b-%Y'
            )
            return (elev_data.groupby('date')
                   .agg({'value': lambda x: round(x.median(), 2)})
                   .rename(columns={'value': 'elev_Ft'})
                   .reset_index())
                   
        except Exception as e:
            self.logger.error(f"Error processing elevation data: {e}")
            raise

    def _process_storage_data(self, data: Dict) -> pd.DataFrame:
        """Process conservation and flood storage data."""
        try:
            # Debug the data structure
            self.logger.debug(f"Data keys: {data.keys()}")
            
            storage_data = []
            if 'value' in data and 'timeSeries' in data['value']:
                time_series = data['value']['timeSeries']
                
                for series in time_series:
                    if ('variable' in series and 
                        'variableDescription' in series['variable']):
                        
                        var_desc = series['variable']['variableDescription']
                        is_conservation = 'Conservation' in var_desc
                        is_flood = 'Flood' in var_desc
                        
                        if (is_conservation or is_flood) and 'values' in series:
                            for value in series['values'][0]['value']:
                                try:
                                    storage_entry = {
                                        'date': pd.to_datetime(value['dateTime']),
                                        'storage_AF' if is_conservation else 'fstorage_AF': 
                                            float(value['value'])
                                    }
                                    storage_data.append(storage_entry)
                                except (ValueError, KeyError) as e:
                                    self.logger.warning(f"Skipping invalid storage value: {e}")
                                    continue
            
            if storage_data:
                df = pd.DataFrame(storage_data)
                # Group by date
                df = (df.groupby('date')
                     .agg({
                         'storage_AF': lambda x: round(x.median(), 0) if 'storage_AF' in df else None,
                         'fstorage_AF': lambda x: round(x.median(), 0) if 'fstorage_AF' in df else None
                     })
                     .reset_index())
                return df
            
            self.logger.warning("No storage data found in API response")
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error processing storage data: {e}")
            self.logger.debug(f"Data structure: {data}")
            raise

    def _fetch_district_data(self, district: str) -> pd.DataFrame:
        """Fetch and process data for all sites in a district."""
        try:
            district_data = []
            district_sites = self.sites[
                (self.sites['District'] == district) & 
                (self.sites['NIDID'].str.contains('TX')) & 
                (self.sites['Loc_ID'] != '2165051')  # Excluding Truscott Brine Lake
            ]
            
            for _, site in district_sites.iterrows():
                # Fetch raw data
                raw_data = self._fetch_reservoir_data(site['Loc_ID'])
                
                # Process elevation and storage
                elev_data = self._process_elevation_data(raw_data)
                storage_data = self._process_storage_data(raw_data)
                
                # Combine data
                site_data = pd.merge(elev_data, storage_data, on='date')
                site_data['locid'] = site['Loc_ID']
                site_data['district'] = district
                site_data['NIDID'] = site['NIDID']
                site_data['name'] = site['Name']
                
                district_data.append(site_data)
                
                self.logger.info(
                    f"Processed {site['Name']} ({site['Loc_ID']}) in {district}"
                )
            
            return pd.concat(district_data, ignore_index=True)
            
        except Exception as e:
            self.logger.error(f"Error processing district {district}: {e}")
            raise

    def _add_julian_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add julian dates using global setup's calendar."""
        try:
            df['year'] = df['date'].dt.year
            df['day_month'] = df['date'].dt.strftime('%m-%d')
            
            def get_julian_day(row):
                is_leap = pd.Timestamp(row['date']).is_leap_year
                day_month_col = 'day_month_leap' if is_leap else 'day_month'
                julian_col = 'julian_index_leap' if is_leap else 'julian_index'
                
                return self.setup.julian_ref.loc[
                    self.setup.julian_ref[day_month_col] == row['day_month'], 
                    julian_col
                ].iloc[0]
            
            df['julian'] = df.apply(get_julian_day, axis=1)
            return df
            
        except Exception as e:
            self.logger.error(f"Error adding julian dates: {e}")
            raise

    def _calculate_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate reservoir statistics and percentiles."""
        try:
            stats = df.groupby(['NIDID', 'julian']).agg({
                'percentStorage': [
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
            
            stats.columns = [
                'NIDID', 'julian', 'Nobs', 'min', 'flow10', 'flow25',
                'flow50', 'flow75', 'flow90', 'max'
            ]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating statistics: {e}")
            raise

    def determine_status(self, row: pd.Series) -> str:
        """Determine reservoir status based on percentiles."""
        if pd.isna(row['percent_storage']):
            return "unknown"
        elif row['percent_storage'] <= row['flow10']:
            return "Extremely Dry"
        elif row['percent_storage'] <= row['flow25']:
            return "Very Dry"
        elif row['percent_storage'] < row['flow50']:
            return "Moderately Dry"
        elif row['percent_storage'] < row['flow75']:
            return "Moderately Wet"
        elif row['percent_storage'] < row['flow90']:
            return "Very Wet"
        else:
            return "Extremely Wet"

    def update_reservoir_data(self):
        """Main method to update all reservoir-related data."""
        try:
            # Fetch new data for all districts
            new_data = pd.concat([
                self._fetch_district_data(district) 
                for district in self.tx_districts
            ])
            
            # Process new data
            new_data = self._add_julian_dates(new_data)
            
            # Calculate percent storage
            new_data['percentStorage'] = (
                new_data['storage_AF'] / new_data['OT_AF'] * 100
            ).round(2)
            
            # Combine with historical data
            all_data = pd.concat([self.old_data, new_data])
            
            # Calculate statistics
            stats = self._calculate_statistics(all_data)
            
            # Save processed data
            self._save_processed_data(all_data, stats)
            
            self.logger.info("Reservoir data update completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating reservoir data: {e}")
            raise

    def _save_processed_data(self, data: pd.DataFrame, stats: pd.DataFrame):
        """Save all processed data files."""
        try:
            # Save main data
            data.to_csv(
                self.reservoir_dir / "usace_dams.csv", 
                index=False
            )
            
            # Filter and save Canyon Lake data
            canyon_lake = data[data['name'] == "Canyon Lake"].copy()
            canyon_lake.to_csv(
                self.reservoir_dir / "all_reservoir_data.csv", 
                index=False
            )
            
            # Save statistics
            stats.to_csv(
                self.reservoir_dir / "all_reservoir_stats.csv", 
                index=False
            )
            
            self.logger.info("All reservoir data files saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving processed data: {e}")
            raise

if __name__ == "__main__":
    processor = ReservoirDataProcessor()
    processor.update_reservoir_data()