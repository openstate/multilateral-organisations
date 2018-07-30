import csv
import os
import sys

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from flask import (
    render_template, request, redirect, url_for, flash, Markup, jsonify
)
from sqlalchemy.sql import func

from app import app, dash_app, db
from app.models import UN, NATO, WorldBank

from datatables import ColumnDT, DataTables

from collections import defaultdict, OrderedDict
from math import ceil
# Use simplejson as it can deal with Decimal
import simplejson as json


# Retrieve either the sum of the amounts or number of transactions (len)
# per country
def get_values(country, organisation, value_type='sum'):
    # If country is 'all' retrieve data of all countries
    if country == 'all':
        if organisation == 'United Nations':
            country_records = UN.query.with_entities(UN.year, UN.amount).all()
        elif organisation == 'NATO':
            country_records = NATO.query.with_entities(
                NATO.year, NATO.amount
            ).all()
        elif organisation == 'World Bank':
            country_records = WorldBank.query.with_entities(
                WorldBank.year, WorldBank.amount
            ).all()
    # Else only retrieve the records of the selected country
    else:
        if organisation == 'United Nations':
            country_records = UN.query.filter_by(
                vendor_country=country
            ).with_entities(UN.year, UN.amount).all()
        elif organisation == 'NATO':
            country_records = NATO.query.filter_by(
                vendor_country=country
            ).with_entities(NATO.year, NATO.amount).all()
        elif organisation == 'World Bank':
            country_records = WorldBank.query.filter_by(
                vendor_country=country
            ).with_entities(WorldBank.year, WorldBank.amount).all()

    records_dict = defaultdict(list)
    for record in country_records:
        records_dict[record[0]].append(record[1])

    values_dict = {}
    for year, amounts in records_dict.items():
        if value_type == 'sum':
            values_dict[year] = sum(amounts)
        elif value_type == 'len':
            values_dict[year] = len(amounts)

    return values_dict


# Create the update for the Dash graph callback
def create_update(country, sum_or_len, numbers_or_percentages, organisation):
    # Retrieve values
    country_values_dict = get_values(country, organisation, sum_or_len)
    if numbers_or_percentages == 'percentages':
        all_values_dict = get_values('all', organisation, sum_or_len)
        for year, amount in country_values_dict.items():
            country_values_dict[year] = amount / all_values_dict[year] * 100

    # Sort the dict by the keys (i.e., year) otherwise the graph line
    # goes crazy
    sorted_country_values_dict = OrderedDict(
        sorted(country_values_dict.items())
    )

    return {
        'data': [go.Scatter(
            x=list(sorted_country_values_dict.keys()),
            y=list(sorted_country_values_dict.values())
        )],
        'layout': go.Layout(
            xaxis={
                'title': 'year'
            },
            yaxis={
                'title': 'amount ($)'
            },
            margin={'l': 80, 'b': 40, 't': 80, 'r': 0},
            title=organisation
        )
    }


## Dash visualisation
# Creates the options list containing all unique countries
values = NATO.query.with_entities(
    NATO.vendor_country
).distinct().all()
values += UN.query.with_entities(
    UN.vendor_country
).distinct().all()
values += WorldBank.query.with_entities(
    WorldBank.vendor_country
).distinct().all()
unique_countries = [
    {'label': i[0], 'value': i[0]} for i in sorted(set(values))
]

# Layout
dash_app.layout = html.Div(children=[
    'Show me for ',
    dcc.Dropdown(
        id='country',
        options=unique_countries,
        value='Netherlands'
    ),
    ' the ',
    dcc.Dropdown(
        id='sum_or_len',
        options=[
            {'label': 'total amount', 'value': 'sum'},
            {'label': 'number of transactions', 'value': 'len'}
        ],
        value='sum'
    ),
    'in',
    dcc.Dropdown(
        id='numbers_or_percentages',
        options=[
            {'label': 'numbers', 'value': 'numbers'},
            {'label': 'percentages', 'value': 'percentages'}
        ],
        value='numbers'
    ),

    dcc.Graph(
        id='un',
        style={'width': '33%', 'display': 'inline-block'},
    ),
    dcc.Graph(
        id='nato',
        style={'width': '33%', 'display': 'inline-block'},
    ),
    dcc.Graph(
        id='world_bank',
        style={'width': '33%', 'display': 'inline-block'},
    ),
])


# Update callback for UN graph
@dash_app.callback(
    dash.dependencies.Output('un', 'figure'),
    [
        dash.dependencies.Input('country', 'value'),
        dash.dependencies.Input('sum_or_len', 'value'),
        dash.dependencies.Input('numbers_or_percentages', 'value')
    ]
)
def update_graph(country, sum_or_len, numbers_or_percentages):
    return create_update(
        country, sum_or_len, numbers_or_percentages, 'United Nations'
    )


# Update callback for NATO graph
@dash_app.callback(
    dash.dependencies.Output('nato', 'figure'),
    [
        dash.dependencies.Input('country', 'value'),
        dash.dependencies.Input('sum_or_len', 'value'),
        dash.dependencies.Input('numbers_or_percentages', 'value')
    ]
)
def update_graph(country, sum_or_len, numbers_or_percentages):
    return create_update(country, sum_or_len, numbers_or_percentages, 'NATO')


# Update callback for World Bank graph
@dash_app.callback(
    dash.dependencies.Output('world_bank', 'figure'),
    [
        dash.dependencies.Input('country', 'value'),
        dash.dependencies.Input('sum_or_len', 'value'),
        dash.dependencies.Input('numbers_or_percentages', 'value')
    ]
)
def update_graph(country, sum_or_len, numbers_or_percentages):
    return create_update(
        country, sum_or_len, numbers_or_percentages, 'World Bank'
    )


@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('index.html', debug=app.debug)


# Provides server side DataTables JSON for UN
@app.route("/datatables-un")
def datatables_un():
    columns = [
        ColumnDT(UN.year),
        ColumnDT(UN.vendor_country),
        ColumnDT(UN.vendor_name),
        ColumnDT(UN.amount),
        ColumnDT(UN.description)
    ]

    # Defining the initial query
    query = db.session.query().select_from(UN)

    # Retrieve the GET parameters coming from the user
    params = request.args.to_dict()

    # Instantiate a DataTable for the query and table needed
    rowTable = DataTables(params, query, columns)

    # returns what is needed by DataTable
    return json.dumps(rowTable.output_result())


# Provides server side DataTables JSON for NATO
@app.route("/datatables-nato")
def datatables_nato():
    columns = [
        ColumnDT(NATO.year),
        ColumnDT(NATO.vendor_country),
        ColumnDT(NATO.vendor_name),
        ColumnDT(NATO.amount),
        ColumnDT(NATO.description)
    ]

    # Defining the initial query
    query = db.session.query().select_from(NATO)

    # Retrieve the GET parameters coming from the user
    params = request.args.to_dict()

    # Instantiate a DataTable for the query and table needed
    rowTable = DataTables(params, query, columns)

    # returns what is needed by DataTable
    return json.dumps(rowTable.output_result())


# Provides server side DataTables JSON for World Bank
@app.route("/datatables-world-bank")
def datatables_world_bank():
    columns = [
        ColumnDT(WorldBank.year),
        ColumnDT(WorldBank.vendor_country),
        ColumnDT(WorldBank.vendor_name),
        ColumnDT(WorldBank.amount),
        ColumnDT(WorldBank.description)
    ]

    # Defining the initial query
    query = db.session.query().select_from(WorldBank)

    # Retrieve the GET parameters coming from the user
    params = request.args.to_dict()

    # Instantiate a DataTable for the query and table needed
    rowTable = DataTables(params, query, columns)

    # returns what is needed by DataTable
    return json.dumps(rowTable.output_result())


@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/data")
def data():
    return render_template('data.html')


if __name__ == "__main__":
    app.run(threaded=True)
