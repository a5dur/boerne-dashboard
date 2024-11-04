**Boerne Water Data Dashboard Manual**

**Overview**

The Internet of Water (IoW) strives to make data more findable, accessible, and usable. The Boerne Water data dashboard demonstrates the value of improved data infrastructure by finding data from multiple sources, accessing those data through API's, and using those data by integrating them into a single dashboard. Additionally, we created new pathways to integrate utility data, improving data access and sharing for water supply and demand for the area of Boerne.

**Running R Scripts**

**Manual Setup Requirements**

**basic\_info.csv Requirements**

The script currently filters the utility shapefile geodatabase for those selected by the state. The file that does this is the basic\_info.csv. If you want to filter the utility layer to include a subset of data, then create the **basic\_info.csv** file. The file **must** contain the following columns:

- pwsid in the format of capital state abbreviation + 7 digits. (e.g. NC0332010)
- utility\_name in the format desired to display on the dashboard (this may come from demand data)
- data = a "yes"/"no" column that tells the dashboard whether to make the utility clickable on the map

**link\_pwsid\_watershed.csv Requirements**

In North Carolina, there was a desire to link the utility to their water supply watershed. We manually created the **link\_pwsid\_watershed.csv** file. This file **must** contain:

- pwsid in the format of capital state abbreviation + 7 digits. (e.g. NC0332010)
- utility\_name in the format desired to display on the dashboard (this may come from demand data)
- ws\_watershed is the name of the water supply watershed in the shapefile provided by the state. There is no unique identifier for the water supply watersheds and so the name must match exactly.

**Script Organization**

The scripts are organized into three main groups:

1. **Environment Setup**
2. - First script sets up R environment, libraries, and variables needed for all other scripts
   **Access Scripts**
3. - Designed to access and build the historic database
   - Take longer to run
   - Only needed when building the initial database
   **Use Scripts**
   - Use the data and access new data since last run
   - Can be run daily, weekly, or monthly to update dashboard data

**Execution Order**

**Full Historic Database Build**

1\. global0\_set\_apis\_libraries.R

2\. access1\_static\_map\_layers.R

3\. access2\_historic\_demand\_data.R

4\. access2\_historic\_streamflow\_data.R

5\. access2\_historic\_precip\_data.R

6\. access2\_historic\_reservoir\_data.R

7\. access2\_historic\_groundwater\_data.R

8\. use1\_demand\_data.R

9\. use1\_streamflow\_data.R

10\. use1\_precip\_data.R

11\. use1\_reservoir\_data.R

12\. use1\_groundwater\_data.R

**Regular Updates Only**

1\. global0\_set\_apis\_libraries.R

2\. use1\_streamflow\_data.R

3\. use1\_demand\_data.R

4\. use1\_precip\_data.R

5\. use1\_reservoir\_data.R

6\. use1\_groundwater\_data.R

**Initial Setup**

1. In R studio, open **global0\_set\_apis\_libraries.R**
   - Change the state abbreviation and fips for your state
   - If you change folder directory names, update swd\_html to save data in appropriate folder
   - The Julian csv file must be in the data folder of the github repository

**Detailed Script Documentation**

**1. Demand Data (use1\_demand\_data.R)**

**Purpose**

Processes water demand data for the City of Boerne's utility system, tracking usage from multiple water sources including groundwater, surface water (Boerne Lake), GBRA supply, and reclaimed water.

**Required Files**

| **File Name**                                   | **Description**                                        |
| ----------------------------------------------- | ------------------------------------------------------ |
| ../data/utility.geojson                         | Utility service area boundaries and system information |
| ../data/demand/historic\_total\_demand.csv      | Historical total water demand data                     |
| ../data/demand/historic\_demand\_by\_source.csv | Historical breakdown of demand by water source         |
| ../data/demand/historic\_reclaimed\_water.csv   | Historical reclaimed water usage data                  |
| ../data/demand/historic\_pop.csv                | Historical population data for service area            |

**Generated Files**

| **File Name**                                         | **Description**                                                 |
| ----------------------------------------------------- | --------------------------------------------------------------- |
| ../data/demand/all\_demand\_by\_source.csv            | Daily demand broken down by source type                         |
| ../data/demand/all\_total\_demand.csv                 | Total daily demand with moving averages                         |
| ../data/demand/all\_demand\_cum.csv                   | Cumulative demand totals by year                                |
| ../data/demand/all\_reclaimed\_water.csv              | Daily reclaimed water usage                                     |
| ../data/demand/all\_reclaimed\_percent\_of\_total.csv | Reclaimed water as percentage of total                          |
| ../data/demand/all\_pop.csv                           | Population data for both City Limits and Water Service Boundary |

**Key Features**

1. **Water Source Tracking**:
2. - Groundwater from local aquifers
   - Surface water from Boerne Lake
   - GBRA (Guadalupe-Blanco River Authority) supply
   - Reclaimed water system
   **Data Processing**:
3. - Converts raw data to Million Gallons per Day (MGD)
   - Calculates 7-day moving averages
   - Identifies peak demand periods
   - Computes cumulative usage
   - Handles missing data and anomalies
   **Analysis Types**:
4. - Daily demand patterns
   - Monthly peak calculations
   - Annual trends
   - Source distribution analysis
   - Reclaimed water utilization
   - Population-based metrics
   **Time Series Features**:
   - Daily data updates
   - Monthly summaries
   - Annual comparisons
   - Seasonal pattern analysis
   - Long-term trend evaluation

**Technical Notes**

1. **Data Collection**:
2. - Sources data from Google Sheets
   - Uses authenticated access
   - Handles multiple data types
   - Processes multiple time periods
   **Calculations**:
3. - Converts units to MGD
   - Calculates moving averages for smoothing
   - Computes 98th percentile for peak demand
   - Determines reclaimed water percentages
   - Handles leap year calculations
   **Quality Control**:
4. - Removes zero-value days without data
   - Validates measurement units
   - Handles missing values
   - Ensures data continuity
   - Manages duplicate entries
   **Population Metrics**:
   - Tracks both city limits and service area populations
   - Enables per capita consumption calculations
   - Supports growth trend analysis
   - Facilitates demand forecasting

**2. Streamflow Data (use1\_streamflow\_data.R)**

**Purpose**

Processes streamflow data from USGS monitoring stations, calculating rolling averages, historical statistics, and current conditions using the USGS National Water Information System (NWIS).

**Required Files**

| **File Name**                                   | **Description**                           |
| ----------------------------------------------- | ----------------------------------------- |
| ../data/streamflow/stream\_gauge\_sites.geojson | Locations and metadata for stream gauges  |
| ../data/streamflow/stream\_gauge\_metadata.csv  | Detailed metadata for monitoring stations |
| ../data/streamflow/historic\_stream\_data.csv   | Historical streamflow measurements        |

**Generated Files**

| **File Name**                                        | **Description**                                       |
| ---------------------------------------------------- | ----------------------------------------------------- |
| ../data/streamflow/all\_stream\_data.csv             | Complete time series of daily streamflow measurements |
| ../data/streamflow/all\_stream\_gauge\_sites.geojson | Stream gauge locations with current conditions        |
| ../data/streamflow/all\_stream\_stats.csv            | Daily flow statistics and status classifications      |
| ../data/streamflow/current\_sites\_status.csv        | Current status by watershed                           |

**Key Features**

1. **Data Collection**:
2. - Uses USGS NWIS Web Services
   - Parameter Code 00060 (discharge in cubic feet per second)
   - Daily mean values (Statistic Code 00003)
   - Real-time data updates
   **Statistical Analysis**:
3. - 7-day moving averages
   - Historical flow percentiles (10th, 25th, 50th, 75th, 90th)
   - Daily flow statistics
   - Period of record calculations
   **Status Classifications**:
4. - Extremely Dry (≤ 10th percentile flow)
   - Very Dry (10th-25th percentile flow)
   - Moderately Dry (25th-50th percentile flow)
   - Moderately Wet (50th-75th percentile flow)
   - Very Wet (75th-90th percentile flow)
   - Extremely Wet (≥ 90th percentile flow)
   **Spatial Analysis**:
   - HUC8 watershed delineation
   - Water supply watershed tracking
   - Geographic distribution of conditions
   - Site-specific trend analysis

**3. Reservoir Data (use1\_reservoir\_data.R)**

**Purpose**

Uses the US Army Corps of Engineers (USACE) API to update reservoir data for Canyon Lake, calculating percent full relative to operational targets.

**Required Files**

| **File Name**                           | **Description**                      |
| --------------------------------------- | ------------------------------------ |
| ../data/reservoirs/usace\_sites.geojson | Location and current conditions      |
| ../data/reservoirs/usace\_dams.csv      | Historic reservoir level data        |
| ./data/julian-daymonth.csv              | Julian day to date format conversion |

**Generated Files**

| **File Name**                               | **Description**                           |
| ------------------------------------------- | ----------------------------------------- |
| ../data/reservoirs/usace\_dams.csv          | Updated historic daily reservoir data     |
| ../data/reservoirs/reservoir\_stats.csv     | Summary statistics of storage percentages |
| ../data/reservoirs/usace\_sites.geojson     | Updated site data with current conditions |
| ../data/reservoirs/all\_reservoir\_data.csv | Filtered data for Canyon Lake             |

**4. Precipitation Data (use1\_precip\_data.R)**

**Purpose**

Processes precipitation data from multiple sources including drought monitoring maps, weather forecasts, and daily measurements.

**Required Files**

| **File Name**                            | **Description**                            |
| ---------------------------------------- | ------------------------------------------ |
| ../data/huc8.geojson                     | Sub-basins in Texas                        |
| ../data/drought/percentAreaHUC.csv       | Historical drought data (from 2000)        |
| ../data/pcp/pcp\_locations\_metadata.csv | Precipitation monitoring stations metadata |
| ../data/pcp/historic\_pcp\_data.csv      | Historical precipitation data              |

**Generated Files**

| **File Name**                                  | **Description**                             |
| ---------------------------------------------- | ------------------------------------------- |
| ../data/drought/current\_drought.geojson       | Current drought conditions map layer        |
| ../data/drought/all\_percentAreaHUC.csv        | Sub-basin drought percentages               |
| ../data/pcp/pcp610forecast.geojson             | 6-10 day precipitation forecast             |
| ../data/pcp/temp610forecast.geojson            | 6-10 day temperature forecast               |
| ../data/pcp/qpf1-7dayforecast.geojson          | 7-day total precipitation forecast          |
| ../data/pcp/pcp\_7day\_obsv.geojson            | Seven-day observed precipitation            |
| ../data/pcp/pcp\_7day\_percent\_normal.geojson | Seven-day percent of normal precipitation   |
| ../data/pcp/all\_pcp\_sites.geojson            | Current conditions at weather stations      |
| ../data/pcp/all\_pcp\_data.csv                 | Complete time series of daily precipitation |
| ../data/pcp/all\_pcp\_months\_total.csv        | Monthly precipitation totals                |
| ../data/pcp/all\_pcp\_cum\_total.csv           | Cumulative precipitation by year            |

**Data Sources**

1. **US Drought Monitor**:
2. - Weekly drought condition updates
   - Drought severity classifications
   - Sub-basin drought percentages
   **Weather Stations**:
3. - NOAA GHCND stations
   - Texas Mesonet API data
   - Synoptic Data API stations including:
     - HADS (Hydrometeorological Automated Data System)
     - TWDB (Texas Water Development Board)
     - EAA (Edwards Aquifer Authority)
     - GBRA (Guadalupe-Blanco River Authority)
     - RAWS (Remote Automated Weather Stations)
   **NOAA Forecasts**:
   - 6-10 day precipitation outlooks
   - 6-10 day temperature outlooks
   - 7-day quantitative precipitation forecasts

**5. Groundwater Data (use1\_groundwater\_data.R)**

**Purpose**

Manages groundwater monitoring data from the Cow Creek Groundwater Conservation District (CCGCD).

**Required Files**

| **File Name**                      | **Description**                           |
| ---------------------------------- | ----------------------------------------- |
| ../data/gw/well\_metadata.csv      | Metadata for monitored groundwater wells  |
| ../data/gw/historic\_gw\_depth.csv | Historical groundwater level measurements |

**Generated Files**

| **File Name**                     | **Description**                              |
| --------------------------------- | -------------------------------------------- |
| ../data/gw/all\_gw\_depth.csv     | Complete time series of daily measurements   |
| ../data/gw/all\_monthly\_avg.csv  | Monthly averages of groundwater depths       |
| ../data/gw/all\_gw\_sites.geojson | Monitoring locations with current conditions |
| ../data/gw/all\_gw\_status.csv    | Daily data with status classifications       |
| ../data/gw/all\_gw\_stats.csv     | Summary statistics by day of year            |
| ../data/gw/all\_gw\_annual.csv    | Annual median groundwater depths             |

**Technical Notes**

1. **Data Collection**:
2. - Retrieves data from Google Sheets using authorized access
   - Processes multiple sheets containing well data
   - Handles missing values and duplicates
   **Temporal Processing**:
3. - Manages leap year calculations
   - Handles irregular measurement intervals
   - Aggregates to monthly averages for sparse data
   - Maintains continuous time series
   **Quality Control**:
4. - Validates measurement types and formats
   - Removes invalid measurements
   - Handles missing data appropriately
   - Flags inactive monitoring locations
   **Geospatial Features**:
   - Converts well locations to geospatial format
   - Creates map layers for visualization
   - Includes current conditions as attributes
   - Enables spatial analysis of aquifer conditions

**6. Water Quality Data (use1\_water\_quality\_data.R)**

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

 
