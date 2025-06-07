from functions import *
from datetime import datetime, timedelta
import dash
from dash import html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd  # Assuming data is in a pandas DataFrame

N_CLICKS = None

df_mps = pd.DataFrame(columns=['Målepunkts ID', 'Info'])
df_mp_data = None

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
    app.run_server(debug=False, host='0.0.0.0', port=8050)
