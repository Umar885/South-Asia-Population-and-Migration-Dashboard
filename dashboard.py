import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import requests


# Function to fetch data from the World Bank API
def fetch_data(country_codes, indicator, start_year, end_year):
    url = f"http://api.worldbank.org/v2/country/{';'.join(country_codes)}/indicator/{indicator}"
    params = {
        'format': 'json',
        'date': f"{start_year}:{end_year}",
        'per_page': 5000
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if len(data) > 1:
            return data[1]  # The second element contains the actual data
        else:
            print(f"No data found for indicator {indicator}!")
            return []
    else:
        print(f"Failed to fetch data for indicator {indicator}. HTTP Status code: {response.status_code}")
        return []


# Function to process and clean the data
def process_data(raw_data):
    if raw_data:
        df = pd.DataFrame(raw_data)
        # Extract relevant columns
        df = df[['countryiso3code', 'date', 'value']]
        df.columns = ['Country Code', 'Year', 'Value']
        # Remove rows with missing values
        df.dropna(inplace=True)
        # Convert data types
        df['Year'] = df['Year'].astype(int)
        df['Value'] = df['Value'].astype(float)
        return df
    else:
        return pd.DataFrame()


# Define parameters
country_codes = ['AFG', 'IND', 'PAK', 'BGD', 'LKA']  # Afghanistan, India, Pakistan, Bangladesh, Sri Lanka
indicators = {
    'Population': 'SP.POP.TOTL',     # Total population
    'Net Migration': 'SM.POP.NETM'  # Net migration
}
start_year = 1960
end_year = 2023

# Fetch and process data for each indicator
all_data = {}
for name, indicator in indicators.items():
    raw_data = fetch_data(country_codes, indicator, start_year, end_year)
    processed_data = process_data(raw_data)
    all_data[name] = processed_data

# Combine the datasets
if all_data:
    population_df = all_data.get('Population', pd.DataFrame())
    migration_df = all_data.get('Net Migration', pd.DataFrame())
    
    # Merge datasets on Country Code and Year
    merged_df = pd.merge(
        population_df, migration_df, 
        on=['Country Code', 'Year'], 
        how='outer', 
        suffixes=('_Population', '_Net Migration')
    )

# Use merged_df as the data source
df = merged_df.copy()

# Dash application
app = dash.Dash(__name__)

# Layout of the dashboard
app.layout = html.Div([
    html.H1("South Asia Population and Migration Dashboard", style={"textAlign": "center"}),

    # Dropdown for multiple country selection
    html.Label("Select Countries:"),
    dcc.Dropdown(
        id="country-dropdown",
        options=[
            {"label": "Afghanistan", "value": "AFG"},
            {"label": "India", "value": "IND"},
            {"label": "Pakistan", "value": "PAK"},
            {"label": "Bangladesh", "value": "BGD"},
            {"label": "Sri Lanka", "value": "LKA"}
        ],
        value=["AFG"],  # Default value
        multi=True,  # Allow multiple selection
        clearable=False
    ),
    
    # Dropdown for year range selection
    html.Label("Select Year Range:"),
    dcc.RangeSlider(
        id="year-range-slider",
        min=1960,
        max=2023,
        step=1,
        marks={year: str(year) for year in range(1960, 2024, 5)},
        value=[1960, 2023],  # Default year range
    ),

    # Line plot for population over years
    dcc.Graph(id="line-plot-population"),

    # Line plot for net migration over years
    dcc.Graph(id="line-plot-migration"),

    # Scatter plot for net migration vs. total population
    dcc.Graph(id="scatter-plot")
])

# Callbacks to update graphs
@app.callback(
    [
        Output("line-plot-population", "figure"), 
        Output("line-plot-migration", "figure"), 
        Output("scatter-plot", "figure")
    ],
    [
        Input("country-dropdown", "value"),
        Input("year-range-slider", "value")
    ]
)
def update_graphs(selected_countries, selected_year_range):
    # Filter data for the selected countries and year range
    filtered_df = df[
        (df["Country Code"].isin(selected_countries)) &
        (df["Year"] >= selected_year_range[0]) &
        (df["Year"] <= selected_year_range[1])
    ]
    
    # Line plot: Population over years
    line_fig_population = px.line(
        filtered_df,
        x="Year",
        y="Value_Population",
        title="Population Over the Years",
        labels={"Value_Population": "Total Population", "Year": "Year"},
        markers=True,
        color="Country Code"
    )
    
    # Line plot: Net Migration over years
    line_fig_migration = px.line(
        filtered_df,
        x="Year",
        y="Value_Net Migration",
        title="Net Migration Over the Years",
        labels={"Value_Net Migration": "Net Migration", "Year": "Year"},
        markers=True,
        color="Country Code"
    )
    
    # Scatter plot: Net Migration vs. Total Population
    scatter_fig = px.scatter(
        filtered_df,
        x="Value_Population",
        y="Value_Net Migration",
        title="Net Migration vs. Total Population",
        labels={"Value_Population": "Total Population", "Value_Net Migration": "Net Migration"},
        size="Value_Population",  # Bubble size
        color="Year",  # Color by year for better visualization
        symbol="Country Code"  # Different symbol for each country
    )
    
    return line_fig_population, line_fig_migration, scatter_fig

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)








