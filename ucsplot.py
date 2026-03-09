import dash
from dash import html, dcc, dash_table
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import os
import plotly.express as px

# --- 1. DATA LOADING ---
# Path to your local CSV
FILE_PATH = 'UCS-Satellite-Database-1-1-2023.csv'

if os.path.exists(FILE_PATH):
    df = pd.read_csv(FILE_PATH, encoding='ISO-8859-1')
    # Cleaning columns (stripping extra spaces from headers)
    df.columns = df.columns.str.strip()
else:
    # Fallback if file is missing
    df = pd.DataFrame(columns=['Users', 'Purpose', 'Count'])

# --- 2. ANALYSIS LOGIC ---


# Extract Launch Year
df['Date of Launch'] = pd.to_datetime(df['Date of Launch'], errors='coerce')
df['Launch_Year'] = df['Date of Launch'].dt.year
df['Launch_Year'] = df['Date of Launch'].dt.year.astype('Int64')

# Cleaner column name for Satellites
df['Satellite_Name'] = df['Name of Satellite, Alternate Names']

# Clean Up User column
df['Clean_Source'] = df['Users'].str.strip()
def categorize_user(val):
    if '/' in val:
        return 'Multi-use'
    elif 'Commercial' in val:
        return 'Commercial'
    elif 'Civil' in val:
        return 'Civil'
    elif 'Government' in val:
        return 'Government'
    elif 'Military' in val:
        return 'Military'
    else:
        return 'Other'

df['Mission_Category'] = df['Clean_Source'].apply(categorize_user)
country_mission_counts = df.groupby(['Country of Operator/Owner', 'Mission_Category']).size().reset_index(name='Count')
# Fix LEO, GEO, MEO designations which are mixed case
df['Class of Orbit'] = df['Class of Orbit'].str.upper()

unique_mission_types = df['Detailed Purpose'].nunique()
num_years = df['Launch_Year'].nunique()
country_counts = df['Country of Operator/Owner'].value_counts().reset_index()
country_counts.columns = ['Country', 'Count']
country_counts_top_ten = country_counts.nlargest(10, "Count")

# Satellites by Country and Contractor
#satellite_counts = 
country_contractor_counts = df.groupby(['Country of Operator/Owner', 'Contractor']).size().reset_index(name='Count')

# Satellites by Contractor
contractor_counts = df.groupby(['Operator/Owner', 'Name of Satellite, Alternate Names']).size().reset_index(name='Count')
contractor_counts.columns = ['Contractor', 'Satellite', 'Count']
selected_contractor = 'Spacex'
myfilter = contractor_counts[contractor_counts['Contractor'] == selected_contractor]


# Satellites by Orbit
orbit_counts = df['Class of Orbit'].value_counts().reset_index()
orbit_counts.columns = ['Orbit', 'Count']

# Satellites by Year and Type
year_orbit_counts = df.groupby(['Launch_Year', 'Class of Orbit']).size().reset_index(name='Count')

# Abbreviated Satellite List
satellite_table = df[['Current Official Name of Satellite', 'Launch_Year', 'Operator/Owner', 'Class of Orbit']]
satellite_table.columns = ['Satellite Name', 'Launch Year',  'Contractor', 'Orbit']

total_records = len(df)

#total_count = df['Count'].sum() if 'Count' in df.columns else 0

fig_country = px.bar(country_counts_top_ten, 
                     x='Count', 
                     y='Country', 
                     labels={'Count': 'Number of Satellites'},
                     orientation='h', 
                     title="Top 10 Countries Launching Satellites", 
                     template="plotly_dark")
fig_country.update_layout(
        title={
            'text': "Top Ten Countries Launching Satellites",
            'y': 0.9,          # Vertical position (0 to 1)
            'x': 0.5,          # Horizontal position (0.5 is the middle)
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 28,             # Increase this number for a bigger font
                'family': "Arial, Bold", # Optional: Change font family
                'color': "white"     # Optional: Change font color
            }
        }
    )
fig_orbits = px.pie(orbit_counts, 
                    values='Count', 
                    names='Orbit', 
                    labels={'Count': 'Number of Satellites'},
                    hole=.7, 
                    title='Satellites by Orbit', 
                    template='plotly_dark')
fig_orbits.update_layout(
        title={
            'text': "Satellite Launches by Orbit Type",
            'y': 0.9,          # Vertical position (0 to 1)
            'x': 0.5,          # Horizontal position (0.5 is the middle)
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 28,             # Increase this number for a bigger font
                'family': "Arial, Bold", # Optional: Change font family
                'color': "white"     # Optional: Change font color
            }
        }
    )

# --- 3. APP SETUP ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE])

def create_kpi_card(title, value, color="primary"):
    return dbc.Card(
        dbc.CardBody([
            html.H5(title, className="card-title text-muted"),
            html.H2(f"{value:,}", className=f"text-{color}")
        ]),
        className="shadow-sm"
    )

@app.callback(
    Output(component_id='graph-with-slider', component_property='figure'), 
    Input(component_id='year-slider', component_property='value'))         


def update_figure(selected_year):
    filtered_df = year_orbit_counts[(year_orbit_counts['Launch_Year'] >= selected_year[0]) & 
                                (year_orbit_counts['Launch_Year'] <= selected_year[1])]
    
  

    fig = px.bar(filtered_df, 
             x="Launch_Year", 
             y="Count",
             labels={'Count': 'Number of Satellites'},            
             color="Class of Orbit", 
             title="Launches per Year by Orbit Type",
             barmode="stack",
             template = 'plotly_dark') 
    
    
    fig.update_layout(
        height=400, # Fixed height prevents the 'growing' bug
        autosize=True,
        hovermode="x unified"
    )

    fig.update_layout(
        title={
            'text': "Satellite Launches by Year ",
            'y': 0.9,          # Vertical position (0 to 1)
            'x': 0.5,          # Horizontal position (0.5 is the middle)
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 28,             # Increase this number for a bigger font
                'family': "Arial, Bold", # Optional: Change font family
                'color': "white"     # Optional: Change font color
            }
        }
    )


    return fig   

@app.callback(
    Output('pie-chart', 'figure'),
    Input('country-dropdown', 'value')
)
def update_chart(selected_country):
    # Filter data based on dropdown
    filtered_df = country_contractor_counts[country_contractor_counts['Country of Operator/Owner'] == selected_country]
    # Find small slices (e.g., less than 5% of the total)
    total = filtered_df['Count'].sum()
    threshold = 0.01 * total 
    
    # Rename small slices to 'Other'
    filtered_df.loc[filtered_df['Count'] < threshold, 'Contractor'] = 'Other'
    
    # Re-aggregate so all 'Other' rows combine
    final_df = filtered_df.groupby('Contractor')['Count'].sum().reset_index()
    
    # Create Pie Chart
    fig = px.pie(
        final_df, 
        values='Count', 
        names='Contractor', 
        labels={'Count': 'Number of Satellites'},
        title=f"Number of Satellites by Country",
        hole=0.3,
        template="plotly_dark"
    )
    fig.update_layout(legend_title_text=f'Satellite Operators for {selected_country}')
    fig.update_layout(
        title={
            'text': "Major Satellite Contractors by Country",
            'y': 0.9,          # Vertical position (0 to 1)
            'x': 0.5,          # Horizontal position (0.5 is the middle)
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 28,             # Increase this number for a bigger font
                'family': "Arial, Bold", # Optional: Change font family
                'color': "white"     # Optional: Change font color
            }
        }
    )
    
    return fig

@app.callback(
    Output('contractor-mission-pie-chart', 'figure'),
    Input('contractor-mission-dropdown', 'value')
)
def update_contractor_mission_chart(selected_country):
    # Filter data based on dropdown
    filtered_df = country_mission_counts[country_mission_counts['Country of Operator/Owner'] == selected_country]
    # Find small slices (e.g., less than 5% of the total)
    total = filtered_df['Count'].sum()
    threshold = 0.01 * total 

        # Rename small slices to 'Other'
    filtered_df.loc[filtered_df['Count'] < threshold, 'Mission_Category'] = 'Other'
    
    # Re-aggregate so all 'Other' rows combine
    final_df = filtered_df.groupby('Mission_Category')['Count'].sum().reset_index()
    

    fig = None 
    # Create Pie Chart
    fig = px.pie(
        final_df, 
        values='Count', 
        names='Mission_Category', 
        title=f"Satellite Mission Categories by Country",
        labels={'Count': 'Number of Satellites'},
        hole=0.3,
        template="plotly_dark"
    )
    fig.update_layout(legend_title_text=f'Mission Categories for {selected_country}')
    fig.update_layout(
        title={
            'text': "Satellite Mission Categories by Country",
            'y': 0.9,          # Vertical position (0 to 1)
            'x': 0.5,          # Horizontal position (0.5 is the middle)
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 28,             # Increase this number for a bigger font
                'family': "Arial, Bold", # Optional: Change font family
                'color': "white"     # Optional: Change font color
            }
        }
    )
    return fig


@app.callback(
    Output('mission-table', 'data'),
    Input('search-input', 'value')
)
def filter_table(search_value):
    # Handle empty search or None
    if not search_value:
        return df.to_dict('records')
    
    # Filter across multiple columns using the OR (|) operator
    filtered_df = satellite_table[
        satellite_table['Satellite Name'].str.contains(search_value, case=False, na=False) |
        satellite_table['Contractor'].str.contains(search_value, case=False, na=False)
    ]
    
    return filtered_df.to_dict('records')
    
app.layout = dbc.Container([
    html.H1("Investigation of Satellite Launches", className="text-center my-4"),
    html.P("Leveraging the UCS Satellite Database found at https://www.ucs.org/resources/satellite-database", className="text-center mb-4"),
    html.Hr(),
    
    # KPI Row
    dbc.Row([
        dbc.Col(create_kpi_card("Total Number of Satellite Missions", total_records, "info"), width=4),
        dbc.Col(create_kpi_card("Unique Satellite Mission Types", unique_mission_types, "info"), width=4),
        dbc.Col(create_kpi_card("Number of Years of Data", num_years, "info"), width=4),
    ], className="mb-4"),

    # Static Figure Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Markdown("""The United States is clearly a leader, primarily due to contributions from Small Sat operators 
                                 including SpaceX which provides Starlink Internet  ."""),  
                    dcc.Graph(figure=fig_country) 
                ])
            ], className="shadow-sm")
        ], width=6),
        # 
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Markdown("""Low Earth Orbit (LEO) satellites orbit at Less than 2000 KM, while Medium Earth Orbit (MEO)
                                 orbit at less than 35,000 KM, and Geosynchronous Earth Orbit (GEO) satellites operate at 35,786 KM"""),
                    dcc.Graph(figure=fig_orbits) 
                ])
            ], className="shadow-sm")
        ], width=6),
    ], className="mb-4"),

    # Show Bar Chart with dual slider
    dbc.Row([
    dbc.Col([
        dcc.Markdown("""Since 2020, LEO satellite launches are greatly outpacing launches of MEO, GEO, or Elliptial orbit spacecraft.  
                     This is due to technology advances that allow for multiple Small Satellite launches per launch vehicle"""),
        dcc.Graph(id='graph-with-slider',
                 style={'height': '450px'} ),
        html.Label("Select Year Range:"),
        dcc.RangeSlider(
            min=year_orbit_counts['Launch_Year'].min(),
            max=year_orbit_counts['Launch_Year'].max(),
            step=None,
            value=[2000, 2020],
            marks={int(year): str(year) for year in year_orbit_counts['Launch_Year'].unique()},
            id='year-slider'
        ),
    ], className="py-3")
]),
    # Show Pie Chart of orbits based on country
    dbc.Row([

        dbc.Col([
            dcc.Markdown("""The increase in satellite launches has a corresponding increase in the number of companies 
                         providing satellite services."""),
            html.Label(
                "Select country:", 
                className="fw-bold text-white fs-4"  
            ),
            dcc.Dropdown(
                id='country-dropdown',
                options=[{'label': i, 'value': i} for i in country_contractor_counts['Country of Operator/Owner'].unique()],
                value='Spain',
                clearable=False
            )
        ], className="mb-3 text-dark"), 
    ], className="py-3"),
    dbc.Row([
 
        dbc.Col([
            dcc.Graph(id='pie-chart')
        ])
    ], align="center"),

    # Show Missions (Civil, Government, Military) based on Country
    dbc.Row([
     
        dbc.Col([
            html.Label(
                "Select country:", 
                className="fw-bold text-white fs-4"  
            ),
            dcc.Dropdown(
                id='contractor-mission-dropdown',
                options=[{'label': i, 'value': i} for i in country_mission_counts['Country of Operator/Owner'].unique()],
                value='Russia',
                clearable=False
            )
        ], className="mb-3 text-dark"), 
    ]),
    dbc.Row([
        dcc.Markdown("""Most countries have a wide mix of commercial, government, and military missions."""),
        dbc.Col([
            dcc.Graph(id='contractor-mission-pie-chart')
        ])
    ], align="center"),


    # Free Text Search of Satellite Name or Contractor
    # Search Row
    dbc.Row([
        dbc.Col([
            dbc.Label("Search satellite name or contractors:",
                     className="fw-bold text-white fs-4" ),
            dbc.Input(
                id='search-input',
                placeholder='Type to filter...',
                type='text',
                value='NASA',
                debounce=True,
                className="mb3 text-dark "
            ),
        ], className="mb-3 text-dark") 
    ]),

    #Table Row
    dbc.Row([
        dbc.Col([
            dash_table.DataTable(
                id='mission-table',
                columns=[{"name": i, "id": i} for i in satellite_table.columns],
                data=satellite_table.to_dict('records'),
                
                style_table={'overflowX': 'auto', 'borderRadius': '15px', 'overflow': 'hidden'},
                #style_cell={'padding': '12px', 'fontFamily': 'sans-serif'},
                #style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold', 'border': '1px solid #dee2e6'},
                style_data={'border': '1px solid #dee2e6'},
style_cell={
        'padding': '12px',
        'fontFamily': 'sans-serif',
        'backgroundColor': '#272B30',  # Slate deep grey
        'color': 'white',              # White text for contrast
        'border': '1px solid #4e5d6c'  # Subdued border color
    },
    
    # 2. Header Styling (Slightly lighter grey to distinguish from data)
    style_header={
        'backgroundColor': '#3A3F44',  # Slate secondary grey
        'fontWeight': 'bold',
        'color': 'white',
        'border': '1px solid #4e5d6c'
    },
                
   
            )
        ], width=12)
    ]), 
    

], fluid=True)

if __name__ == '__main__':
    app.run(debug=True, port=8080,jupyter_mode="external")

