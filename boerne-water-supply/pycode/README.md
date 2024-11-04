# Boerne Water Data Dashboard Manual

## Table of Contents
- [Overview](#overview)
- [Running R Scripts](#running-r-scripts)
  - [Manual Setup Requirements](#manual-setup-requirements)
  - [Script Organization](#script-organization)
  - [Execution Order](#execution-order)
  - [Initial Setup](#initial-setup)
- [Detailed Script Documentation](#detailed-script-documentation)
  - [1. Demand Data](#1-demand-data)
  - [2. Streamflow Data](#2-streamflow-data)
  - [3. Reservoir Data](#3-reservoir-data)
  - [4. Precipitation Data](#4-precipitation-data)
  - [5. Groundwater Data](#5-groundwater-data)
  - [6. Water Quality Data](#6-water-quality-data)

## Overview

The Internet of Water (IoW) strives to make data more findable, accessible, and usable. The Boerne Water data dashboard demonstrates the value of improved data infrastructure by finding data from multiple sources, accessing those data through API's, and using those data by integrating them into a single dashboard. Additionally, we created new pathways to integrate utility data, improving data access and sharing for water supply and demand for the area of Boerne.

## Running R Scripts

### Manual Setup Requirements

#### basic_info.csv Requirements

The script currently filters the utility shapefile geodatabase for those selected by the state. The file that does this is the basic_info.csv. If you want to filter the utility layer to include a subset of data, then create the **basic_info.csv** file. The file **must** contain the following columns:

- pwsid in the format of capital state abbreviation + 7 digits. (e.g. NC0332010)
- utility_name in the format desired to display on the dashboard (this may come from demand data)
- data = a "yes"/"no" column that tells the dashboard whether to make the utility clickable on the map

#### link_pwsid_watershed.csv Requirements

In North Carolina, there was a desire to link the utility to their water supply watershed. We manually created the **link_pwsid_watershed.csv** file. This file **must** contain:

- pwsid in the format of capital state abbreviation + 7 digits. (e.g. NC0332010)
- utility_name in the format desired to display on the dashboard (this may come from demand data)
- ws_watershed is the name of the water supply watershed in the shapefile provided by the state. There is no unique identifier for the water supply watersheds and so the name must match exactly.

### Script Organization

The scripts are organized into three main groups:

1. **Environment Setup**
   - First script sets up R environment, libraries, and variables needed for all other scripts

2. **Access Scripts**
   - Designed to access and build the historic database
   - Take longer to run
   - Only needed when building the initial database

3. **Use Scripts**
   - Use the data and access new data since last run
   - Can be run daily, weekly, or monthly to update dashboard data

### Execution Order

#### Full Historic Database Build

1. global0_set_apis_libraries.R
2. access1_static_map_layers.R
3. access2_historic_demand_data.R
4. access2_historic_streamflow_data.R
5. access2_historic_precip_data.R
6. access2_historic_reservoir_data.R
7. access2_historic_groundwater_data.R
8. use1_demand_data.R
9. use1_streamflow_data.R
10. use1_precip_data.R
11. use1_reservoir_data.R
12. use1_groundwater_data.R

#### Regular Updates Only

1. global0_set_apis_libraries.R
2. use1_streamflow_data.R
3. use1_demand_data.R
4. use1_precip_data.R
5. use1_reservoir_data.R
6. use1_groundwater_data.R

### Initial Setup

1. In R studio, open **global0_set_apis_libraries.R**
   - Change the state abbreviation and fips for your state
   - If you change folder directory names, update swd_html to save data in appropriate folder
   - The Julian csv file must be in the data folder of the github repository

## Detailed Script Documentation

### 1. Demand Data (use1_demand_data.R)

#### Purpose

Processes water demand data for the City of Boerne's utility system, tracking usage from multiple water sources including groundwater, surface water (Boerne Lake), GBRA supply, and reclaimed water.

#### Required Files

| File Name | Description |
|-----------|-------------|
| ../data/utility.geojson | Utility service area boundaries and system information |
| ../data/demand/historic_total_demand.csv | Historical total water demand data |
| ../data/demand/historic_demand_by_source.csv | Historical breakdown of demand by water source |
| ../data/demand/historic_reclaimed_water.csv | Historical reclaimed water usage data |
| ../data/demand/historic_pop.csv | Historical population data for service area |

#### Generated Files

| File Name | Description |
|-----------|-------------|
| ../data/demand/all_demand_by_source.csv | Daily demand broken down by source type |
| ../data/demand/all_total_demand.csv | Total daily demand with moving averages |
| ../data/demand/all_demand_cum.csv | Cumulative demand totals by year |
| ../data/demand/all_reclaimed_water.csv | Daily reclaimed water usage |
| ../data/demand/all_reclaimed_percent_of_total.csv | Reclaimed water as percentage of total |
| ../data/demand/all_pop.csv | Population data for both City Limits and Water Service Boundary |

#### Key Features

1. **Water Source Tracking**:
   - Groundwater from local aquifers
   - Surface water from Boerne Lake
   - GBRA (Guadalupe-Blanco River Authority) supply
   - Reclaimed water system

2. **Data Processing**:
   - Converts raw data to Million Gallons per Day (MGD)
   - Calculates 7-day moving averages
   - Identifies peak demand periods
   - Computes cumulative usage
   - Handles missing data and anomalies

3. **Analysis Types**:
   - Daily demand patterns
   - Monthly peak calculations
   - Annual trends
   - Source distribution analysis
   - Reclaimed water utilization
   - Population-based metrics

4. **Time Series Features**:
   - Daily data updates
   - Monthly summaries
   - Annual comparisons
   - Seasonal pattern analysis
   - Long-term trend evaluation

#### Technical Notes

1. **Data Collection**:
   - Sources data from Google Sheets
   - Uses authenticated access
   - Handles multiple data types
   - Processes multiple time periods

2. **Calculations**:
   - Converts units to MGD
   - Calculates moving averages for smoothing
   - Computes 98th percentile for peak demand
   - Determines reclaimed water percentages
   - Handles leap year calculations

3. **Quality Control**:
   - Removes zero-value days without data
   - Validates measurement units
   - Handles missing values
   - Ensures data continuity
   - Manages duplicate entries

4. **Population Metrics**:
   - Tracks both city limits and service area populations
   - Enables per capita consumption calculations
   - Supports growth trend analysis
   - Facilitates demand forecasting

### 2. Streamflow Data (use1_streamflow_data.R)

#### Purpose

Processes streamflow data from USGS monitoring stations, calculating rolling averages, historical statistics, and current conditions using the USGS National Water Information System (NWIS).

#### Required Files

| File Name | Description |
|-----------|-------------|
| ../data/streamflow/stream_gauge_sites.geojson | Locations and metadata for stream gauges |
| ../data/streamflow/stream_gauge_metadata.csv | Detailed metadata for monitoring stations |
| ../data/streamflow/historic_stream_data.csv | Historical streamflow measurements |

#### Generated Files

| File Name | Description |
|-----------|-------------|
| ../data/streamflow/all_stream_data.csv | Complete time series of daily streamflow measurements |
| ../data/streamflow/all_stream_gauge_sites.geojson | Stream gauge locations with current conditions |
| ../data/streamflow/all_stream_stats.csv | Daily flow statistics and status classifications |
| ../data/streamflow/current_sites_status.csv | Current status by watershed |

#### Key Features

1. **Data Collection**:
   - Uses USGS NWIS Web Services
   - Parameter Code 00060 (discharge in cubic feet per second)
   - Daily mean values (Statistic Code 00003)
   - Real-time data updates

2. **Statistical Analysis**:
   - 7-day moving averages
   - Historical flow percentiles (10th, 25th, 50th, 75th, 90th)
   - Daily flow statistics
   - Period of record calculations

3. **Status Classifications**:
   - Extremely Dry (≤ 10th percentile flow)
   - Very Dry (10th-25th percentile flow)
   - Moderately Dry (25th-50th percentile flow)
   - Moderately Wet (50th-75th percentile flow)
   - Very Wet (75th-90th percentile flow)
   - Extremely Wet (≥ 90th percentile flow)

4. **Spatial Analysis**:
   - HUC8 watershed delineation
   - Water supply watershed tracking
   - Geographic distribution of conditions
   - Site-specific trend analysis

3. Reservoir Data (use1_reservoir_data.R)
Purpose
Uses the US Army Corps of Engineers (USACE) API to update reservoir data for Canyon Lake, calculating percent full relative to operational targets.
Required Files
File NameDescription../data/reservoirs/usace_sites.geojsonLocation and current conditions../data/reservoirs/usace_dams.csvHistoric reservoir level data./data/julian-daymonth.csvJulian day to date format conversion
Generated Files
File NameDescription../data/reservoirs/usace_dams.csvUpdated historic daily reservoir data../data/reservoirs/reservoir_stats.csvSummary statistics of storage percentages../data/reservoirs/usace_sites.geojsonUpdated site data with current conditions../data/reservoirs/all_reservoir_data.csvFiltered data for Canyon Lake
4. Precipitation Data (use1_precip_data.R)
Purpose
Processes precipitation data from multiple sources including drought monitoring maps, weather forecasts, and daily measurements.
Required Files
File NameDescription../data/huc8.geojsonSub-basins in Texas../data/drought/percentAreaHUC.csvHistorical drought data (from 2000)../data/pcp/pcp_locations_metadata.csvPrecipitation monitoring stations metadata../data/pcp/historic_pcp_data.csvHistorical precipitation data
Generated Files
File NameDescription../data/drought/current_drought.geojsonCurrent drought conditions map layer../data/drought/all_percentAreaHUC.csvSub-basin drought percentages../data/pcp/pcp610forecast.geojson6-10 day precipitation forecast../data/pcp/temp610forecast.geojson6-10 day temperature forecast../data/pcp/qpf1-7dayforecast.geojson7-day total precipitation forecast../data/pcp/pcp_7day_obsv.geojsonSeven-day observed precipitation../data/pcp/pcp_7day_percent_normal.geojsonSeven-day percent of normal precipitation../data/pcp/all_pcp_sites.geojsonCurrent conditions at weather stations../data/pcp/all_pcp_data.csvComplete time series of daily precipitation../data/pcp/all_pcp_months_total.csvMonthly precipitation totals../data/pcp/all_pcp_cum_total.csvCumulative precipitation by year
Data Sources

US Drought Monitor:

Weekly drought condition updates
Drought severity classifications
Sub-basin drought percentages


Weather Stations:

NOAA GHCND stations
Texas Mesonet API data
Synoptic Data API stations including:

HADS (Hydrometeorological Automated Data System)
TWDB (Texas Water Development Board)
EAA (Edwards Aquifer Authority)
GBRA (Guadalupe-Blanco River Authority)
RAWS (Remote Automated Weather Stations)




NOAA Forecasts:

6-10 day precipitation outlooks
6-10 day temperature outlooks
7-day quantitative precipitation forecasts



5. Groundwater Data (use1_groundwater_data.R)
Purpose
Manages groundwater monitoring data from the Cow Creek Groundwater Conservation District (CCGCD).
Required Files
File NameDescription../data/gw/well_metadata.csvMetadata for monitored groundwater wells../data/gw/historic_gw_depth.csvHistorical groundwater level measurements
Generated Files
File NameDescription../data/gw/all_gw_depth.csvComplete time series of daily measurements../data/gw/all_monthly_avg.csvMonthly averages of groundwater depths../data/gw/all_gw_sites.geojsonMonitoring locations with current conditions../data/gw/all_gw_status.csvDaily data with status classifications../data/gw/all_gw_stats.csvSummary statistics by day of year../data/gw/all_gw_annual.csvAnnual median groundwater depths
Technical Notes

Data Collection:

Retrieves data from Google Sheets using authorized access
Processes multiple sheets containing well data
Handles missing values and duplicates


Temporal Processing:

Manages leap year calculations
Handles irregular measurement intervals
Aggregates to monthly averages for sparse data
Maintains continuous time series


Quality Control:

Validates measurement types and formats
Removes invalid measurements
Handles missing data appropriately
Flags inactive monitoring locations


Geospatial Features:

Converts well locations to geospatial format
Creates map layers for visualization
Includes current conditions as attributes
Enables spatial analysis of aquifer conditions



6. Water Quality Data (use1_water_quality_data.R)
Purpose
Processes water quality monitoring data from multiple sampling locations in the Boerne area.
Required Files
File NameDescription../data/quality/boerne_water_quality.csvHistorical water quality measurements../data/quality/water_quality_sites.geojsonMonitoring station locations and metadata
Generated Files
File NameDescription../data/quality/all_boerne_water_quality.csvComplete time series of measurements
Parameters Monitored

Physical Parameters:

Water Temperature (°C)
Air Temperature (°C)
Conductivity (µs/cm)
Secchi Disk Transparency (m)
Sample Depth (m)

**Purpose**

Processes water quality monitoring data from multiple sampling locations in the Boerne area.

**Required Files**

| **File Name**                                 | **Description**                           |
| --------------------------------------------- | ----------------------------------------- |
| ../data/quality/boerne\_water\_quality.csv    | Historical water quality measurements     |
| ../data/quality/water\_quality\_sites.geojson | Monitoring station locations and metadata |

**Generated Files**

| **File Name**                                   | **Description**                      |
| ----------------------------------------------- | ------------------------------------ |
| ../data/quality/all\_boerne\_water\_quality.csv | Complete time series of measurements |

**Parameters Monitored**

1. **Physical Parameters**:
2. - Water Temperature (°C)
   - Air Temperature (°C)
   - Conductivity (µs/cm)
   - Secchi Disk Transparency (m)
   - Sample Depth (m)
   **Chemical Parameters**:
3. - Dissolved Oxygen (mg/L)
   - Nitrate-Nitrogen (mg/L or ppm)
   **Biological Parameters**:
4. - E. Coli Average counts
   **Site Characteristics**:
   - Flow Severity
   - Stream Segment information

**Monitoring Locations**

The script processes data from eleven specific monitoring stations:

- Site 12600
- Site 15126
- Site 20823
- Site 80186
- Site 80230
- Site 80904
- Site 80966
- Site 81596
- Site 81641
- Site 81671
- Site 81672

**Technical Implementation**

1. **Data Collection**:
   - Sources data from Google Sheets
   - Uses authenticated access
   - Coordinates with geospatial site information
   - Maintains site metadata

 
