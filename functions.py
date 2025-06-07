import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from pyeloverblik import Eloverblik
from geopy.geocoders import Nominatim


# def fetch_eloverblik_dataframe(days=365):
#     data_til_net = fetch_raw_eloverblik_data(MP_TIL_NET, days=days)
#     df_til_net = _data_to_dataframe(data_til_net)

#     data_fra_net = fetch_raw_eloverblik_data(MP_FRA_NET, days=days)
#     df_fra_net = _data_to_dataframe(data_fra_net)

#     return df_til_net.join(df_fra_net)


# def fetch_raw_eloverblik_data(mp, days=365):

#     to_date = datetime.now()
#     from_date = datetime.now()-timedelta(days=days)

#     client = Eloverblik(REFRESH_TOKEN)
#     data_out = client.get_time_series(
#         mp, from_date=from_date, to_date=to_date, aggregation='Hour')

#     return json.loads(data_out.body)


def _data_to_dataframe(data):
    df_out = pd.DataFrame()
    measure_series = data[0]["MyEnergyData_MarketDocument"]["TimeSeries"]

    for timeseries in measure_series:
        days = timeseries["Period"]
        mrid = timeseries["mRID"]

        for day in days:
            start_date = day["timeInterval"]["start"]
            end_date = day["timeInterval"]["end"]

            # Generate a date range with hourly frequency
            date_range = pd.date_range(
                start=start_date, end=end_date, freq='H')[:-1]
            measurement_data = [entry["out_Quantity.quantity"]
                                for entry in day["Point"]]

            # Create a DataFrame with the date range
            df = pd.DataFrame(data=measurement_data,
                              index=date_range, columns=[mrid])
            df_out = pd.concat([df_out, df])
        df_out[mrid] = pd.to_numeric(df_out[mrid])
    return df_out


# NEw

# https://api.eloverblik.dk/CustomerApi/swagger/index.html
# https://helmstedt.dk/2022/03/eldata-fra-eloverblik-dk-med-python/

# Get data access token for subsequent requests
def _get_headers(token):
    get_data_access_token_url = 'https://api.eloverblik.dk/CustomerApi/api/token'
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + token,
    }

    response = requests.get(get_data_access_token_url, headers=headers)
    data_access_token = response.json()['result']

    # Get id of first meter - edit if you have more than one meter
    metering_points_url = 'https://api.eloverblik.dk/CustomerApi/api/meteringpoints/meteringpoints'
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + data_access_token,
    }

    return headers


def get_metering_points(token):

    # Get id of first meter - edit if you have more than one meter
    metering_points_url = 'https://api.eloverblik.dk/CustomerApi/api/meteringpoints/meteringpoints'
    headers = _get_headers(token)
    resp = requests.get(metering_points_url, headers=headers)
    print(resp)
    if resp is None or resp.status_code != 200:
        raise Exception("Could not fetch data from Eloverblik.dk")
    meters = resp.json()['result']
    return meters


def _get_metering_data(token, metering_point_id, date_from, date_to):

    # Get id of first meter - edit if you have more than one meter
    metering_points_url = 'https://api.eloverblik.dk/CustomerApi/api/meteringpoints/meteringpoints'
    headers = _get_headers(token)

    # Try to get data
    meter_data = 'https://api.eloverblik.dk/CustomerApi/api/meterdata/gettimeseries/'
    timeseries_data = {
        'dateFrom': date_from,
        'dateTo': date_to,
        'aggregation': 'Actual'
    }

    meter_data_url = meter_data + timeseries_data['dateFrom'] + '/' + \
        timeseries_data['dateTo'] + '/' + timeseries_data['aggregation']

    meter_json = {
        "meteringPoints": {
            "meteringPoint": [
                metering_point_id
            ]
        }
    }

    meter_data_request = requests.post(
        meter_data_url, headers=headers, json=meter_json)

    return meter_data_request.json()['result']


def get_metering_dataframe(token, metering_point_id, date_from, date_to):
    metering_data = _get_metering_data(token, metering_point_id, date_from, date_to)
    df = _data_to_dataframe(metering_data)
    return df

def get_metering_charges(token, metering_point_id):
    headers = _get_headers(token)

    meter_json = {
        "meteringPoints": {
            "meteringPoint": [
                metering_point_id
            ]
        }
    }

    # Charges
    charges_data = 'https://api.eloverblik.dk/CustomerApi/api/meteringpoints/meteringpoint/getcharges'
    charges_data_request = requests.post(
        charges_data, headers=headers, json=meter_json)

    return charges_data_request.json()['result']


def _geocode_address(address):
    geolocator = Nominatim(user_agent="eloverblik-solceller")
    location = geolocator.geocode(address)
    if location is None:
        raise Exception("Kunne ikke finde adressen")
    return location.latitude, location.longitude


def simulate_pv_production(address, start_date, end_date, pv_size_kw, orientation="Syd", tilt=35):
    lat, lon = _geocode_address(address)
    orientation_map = {
        "Syd": 180,
        "Øst": 90,
        "Vest": 270,
        "Syd-Øst": 135,
        "Syd-Vest": 225,
    }
    azimuth = orientation_map.get(orientation, 180)

    start_year = pd.to_datetime(start_date).year
    end_year = pd.to_datetime(end_date).year

    url = (
        "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc?"
        f"lat={lat}&lon={lon}&startyear={start_year}&endyear={end_year}&"
        f"outputformat=json&peakpower={pv_size_kw}&loss=14&angle={tilt}&aspect={azimuth}&"
        "pvtechchoice=crystSi&mountingplace=building&pvcalculation=1"
    )

    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data["outputs"]["hourly"])
    df["time"] = pd.to_datetime(df["time"].str.replace(":", ""), format="%Y%m%d%H%M")
    df = df[(df["time"] >= pd.to_datetime(start_date)) & (df["time"] <= pd.to_datetime(end_date))]
    df.set_index("time", inplace=True)
    df["P"] = pd.to_numeric(df["P"])
    return df[["P"]]
