from functions import *
from dmi_cache import start_dmi_cache_worker, get_cached_date_range
from datetime import datetime, timedelta
import dash
from dash import html, dcc, Input, Output, State

import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd  # Assuming data is in a pandas DataFrame

N_CLICKS = None

df_mps = pd.DataFrame(columns=['Målepunkts ID', 'Info'])
df_mp_data = None

# Determine available weather data range from cache
cached_range = get_cached_date_range()
if cached_range:
    pv_min_date, pv_max_date = cached_range
else:
    pv_min_date = datetime.utcnow().date() - timedelta(days=30)
    pv_max_date = datetime.utcnow().date()

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.Br(),
    dbc.Card([
        dbc.CardHeader("Vælg rådata fra Eloverblik.dk"),
        dbc.CardBody(
            [
                html.Div([
                    dbc.Alert(["Hent dine elmålerdata fra ",
                               html.A("Eloverblik.dk",
                                      href="https://eloverblik.dk/"),
                               ".",
                               html.Br(),
                               "Vi ønsker at begrænse antal af API kald til rådata, da disse tager lang at processere. "
                               ], color="primary")
                ]),
                html.Br(),

                html.Div([
                    html.H6("1) Indsæt API nøgle fra eloverblik.dk"),
                    dbc.InputGroup([
                        dbc.Input(id='input-apikey', type='text',
                                  placeholder='...'),
                        dbc.Button('Gem API key',
                                   id='save-apikey-button', n_clicks=0, color='secondary'),
                       dbc.Button('Søg på Eloverblik.dk',
                               id='fetch-measurepoints-button', n_clicks=0),            
                    ]),
                    html.Br(),
                ]),
                html.Br(),

                html.Div([
                    html.H6("3) Vælg forbrugsmålepunkt"),
                    
                    html.Br(),
                    html.Br(),
                    dcc.Loading(id='table-placeholder', children=[dbc.Alert(
                        "Kendte målepunkter vises her, når at de er hentet korrekt.", color="info")]),
                    html.Br(),
                    dcc.Dropdown(
                        id="dropdown-measurepoints",
                        options=[],
                        placeholder="Vælg et forbrugsmålepunkt.."
                    ),
                ]),
                html.Br(),
                html.Div([
                    html.H6("4) Hent forbrugs rådata"),
                    html.Br(),
                    dcc.DatePickerRange(
                        id='date-picker-range',
                        start_date=datetime.now()-timedelta(days=30),
                        end_date=datetime.now(),
                        display_format="YYYY-MM-DD"
                    ),
                    html.Br(),
                    html.Br(),
                    dbc.Button('Hent data',
                               id='fetch-data-button', n_clicks=0),
                    dcc.Loading(id='consumption-graph-placeholder', children=[dbc.Alert(
                        "Data vises her, når at de er hentet korrekt.", color="info")])
                ]),
            ])

    ]),
    dcc.Store(id='eloverblik_api_key', storage_type='local'),
    dcc.Store(id='eloverblik_metering_points'),
    dcc.Store(id='eloverblik_selected_metering_point'),
    dcc.Store(id='eloverblik_consumption_data'),
    dcc.Store(id='eloverblik_production_data'),
    dcc.Store(id='pv_configuration', storage_type='local'),
    dcc.Store(id='pv_production_data'),

    html.Br(),

    dbc.Card([
        dbc.CardHeader("Indtast solcelle- og batterioplysninger"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(
                    dbc.InputGroup([
                        dbc.InputGroupText("Solcelle størrelse (kW)"),
                        dbc.Input(id="input-pv-size", type="number", min=0)
                    ]),
                    md=4
                ),
                dbc.Col(
                    dbc.InputGroup([
                        dbc.InputGroupText("Placering"),
                        dcc.Dropdown(
                            id="dropdown-orientation",
                            options=[
                                {"label": o, "value": o}
                                for o in ["Syd", "Øst", "Vest", "Syd-Øst", "Syd-Vest"]
                            ],
                            placeholder="Vælg orientering"
                        )
                    ]),
                    md=4
                ),
                dbc.Col(
                    dbc.InputGroup([
                        dbc.InputGroupText("Batteri størrelse (kWh)"),
                        dbc.Input(id="input-battery-size", type="number", min=0)
                    ]),
                    md=4
                ),
            ]),
            html.Br(),
            dbc.InputGroup([
                dbc.InputGroupText("Adresse"),
                dbc.Input(id="input-address", type="text", placeholder="F.eks. 'Gothersgade 1, København'")
            ]),
            html.Br(),
            dbc.Button("Gem solcelleinfo",
                       id="save-pv-button", n_clicks=0, color="secondary"),
            html.Br(),
            html.Div(id="pv-config-summary"),
            html.Br(),
            html.H6("Periode for solcellevejr"),
            dcc.DatePickerRange(
                id='pv-date-picker-range',
                start_date=pv_min_date,
                end_date=pv_max_date,
                min_date_allowed=pv_min_date,
                max_date_allowed=pv_max_date,
                display_format="YYYY-MM-DD"
            ),
            html.Br(),
            dbc.Button("Simulér produktion",
                       id="simulate-pv-button", n_clicks=0, color="primary"),
            html.Br(),
            dcc.Loading(id='pv-production-result', children=[dbc.Alert(
                "Resultat vises her efter beregning", color="info")])
        ])
    ]),

    html.Br(),

    dbc.Card([
        dbc.CardHeader("Analysér data!"),
        dbc.CardBody([
            dbc.Col(dcc.Graph(id='bar-chart'))
        ])
    ]),


], fluid = True)


@ app.callback(
    Output('eloverblik_api_key', 'data'),
    Input('save-apikey-button', 'n_clicks'),
    State('input-apikey', 'value'),
    prevent_initial_call = True
)
def save_data_to_cache(n_clicks, api_key):
    """
    Callback for saving API key for Eloverblik.dk in browser.
    """
    if n_clicks:
        return api_key
    else:
        return dash.no_update


@ app.callback(
    Output('input-apikey', 'value'),
    Input('eloverblik_api_key', 'data')
)
def display_saved_data(value):
    """
    Callback for fetching API key for Eloverblik.dk in browser if saved.
    """
    if value is not None:
        return value
    else:
        return ''


@ app.callback(
    Output('eloverblik_metering_points', 'data'),
    Output('table-placeholder', 'children'),
    Output('dropdown-measurepoints', 'options'),
    Input('fetch-measurepoints-button', 'n_clicks'),
    State('input-apikey', 'value')

)
def get_metering_points_on_click(n_clicks, token):
    """
    Save json data
    """
    metering_points = []
    options = {}
    table = None

    print(token)

    if token is not None and n_clicks:
        print("here")
        metering_points = get_metering_points(token)

        print(metering_points)

        df_mps = pd.DataFrame(metering_points)[
            ['meteringPointId', 'typeOfMP', 'balanceSupplierName', 'streetName', 'buildingNumber', 'cityName']]

        table = dbc.Table.from_dataframe(
            df_mps, id = 'table-measurepoints', striped = True, bordered = True)

        options = [{'label': "{} ({})".format(row['meteringPointId'], row['typeOfMP']),
                    'value': row['meteringPointId']} for index, row in df_mps.iterrows()]

    return (metering_points, table, options)


@ app.callback(
    Output('eloverblik_selected_metering_point', 'data'),
    Input('dropdown-measurepoints', 'value')

)
def get_eloverblik_raw_data_1(metering_point):
    selected_metering_point = None

    if (metering_point is not None):
        selected_metering_point = metering_point

    return (selected_metering_point)


@ app.callback(
    Output('consumption-graph-placeholder', 'children'),
    Input('eloverblik_selected_metering_point', 'data'),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date'),
    State('eloverblik_api_key', 'data'),


)
def get_eloverblik_raw_data_2(selected_metering_point, start_date, end_date, token):
    graph = None

    if (selected_metering_point is not None):
        df_mp_data = get_metering_dataframe(
            token, selected_metering_point, start_date, end_date)
        
        df_monthly = df_mp_data.resample('D').sum()

        print(df_monthly)

        fig = px.bar(df_monthly)
        graph = dcc.Graph(figure=fig)
        
    return graph


@ app.callback(
    Output('pv_configuration', 'data'),
    Output('pv-config-summary', 'children'),
    Input('save-pv-button', 'n_clicks'),
    State('input-pv-size', 'value'),
    State('dropdown-orientation', 'value'),
    State('input-battery-size', 'value'),
    prevent_initial_call=True
)
def save_pv_configuration(n_clicks, pv_size, orientation, battery_size):
    if n_clicks:
        data = {
            'pv_size_kw': pv_size,
            'orientation': orientation,
            'battery_size_kwh': battery_size
        }
        summary = dbc.Alert(
            f"Gemte solcelleinfo: {pv_size} kW, {orientation}, {battery_size} kWh",
            color='success'
        )
        return data, summary
    return dash.no_update, dash.no_update


@app.callback(
    Output('input-pv-size', 'value'),
    Output('dropdown-orientation', 'value'),
    Output('input-battery-size', 'value'),
    Output('pv-config-summary', 'children'),
    Input('pv_configuration', 'data')
)
def load_pv_configuration(data):
    if data:
        pv_size = data.get('pv_size_kw')
        orientation = data.get('orientation')
        battery_size = data.get('battery_size_kwh')
        summary = dbc.Alert(
            f"Gemte solcelleinfo: {pv_size} kW, {orientation}, {battery_size} kWh",
            color='success'
        )
        return pv_size, orientation, battery_size, summary
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output('pv-production-result', 'children'),
    Output('pv_production_data', 'data'),
    Input('simulate-pv-button', 'n_clicks'),
    State('input-address', 'value'),
    State('input-pv-size', 'value'),
    State('dropdown-orientation', 'value'),
    State('pv-date-picker-range', 'start_date'),
    State('pv-date-picker-range', 'end_date'),
    prevent_initial_call=True
)
def simulate_pv(n_clicks, address, pv_size, orientation, start_date, end_date):
    if n_clicks and address and pv_size and orientation:
        df = simulate_pv_production(address, start_date, end_date,
                                    pv_size, orientation)
        df_daily = df.resample('D').sum()
        fig = px.line(df_daily, y='P', labels={'P': 'kWh'})
        return dcc.Graph(figure=fig), df.to_json(date_format='iso')
    return dash.no_update, dash.no_update


# @app.callback(
#     Output('bar-chart', 'figure'),
#     [Input('date-picker-range', 'start_date'),
#      Input('date-picker-range', 'end_date')]
# )
# def update_graph(n_clicks, start_date, end_date, number):

#     if (n_clicks is not None) or (n_clicks is not N_CLICKS):
#         # Here, you can include the logic to process the number input
#         data = fetch_eloverblik_dataframe(days=90)
#         N_CLICKS = n_clicks

#     print(data.head())

#     print(start_date, end_date the logic to process the number input
#         data = fetch_eloverblik_dataframe(days=90)
#         N_CLICKS = n_clicks

#     print(data.head())

#     new_start_date = data.index.min().strftime('%Y-%m-%d')
#     new_end_date = data.index.max().strftime('%Y-%m-%d')

#     return (new_start_date, new_end_date)e)

#     filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]
#     fig = px.bar(filtered_data, x=filtered_data.index, y=filtered_data.columns[0])
#     return fig


# @app.callback(
#     [Output('date-picker-range', 'start_date'),
#     Output('date-picker-range', 'end_date')],
#     [Input('submit-button', 'n_clicks'),
#      Input('input-number', 'value')]
# )
# def update_date_range(n_clicks, start_date, end_date, number):
#     if (n_clicks is not None) or (n_clicks is not N_CLICKS):
#         # Here, you can includ
if __name__ == '__main__':
    start_dmi_cache_worker()
    app.run(debug=False, host='0.0.0.0', port=8050)
