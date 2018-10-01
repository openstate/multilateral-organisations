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

from app import app, dash_app, db
from app.models import UN, NATO, WorldBank

from datatables import ColumnDT, DataTables

from collections import defaultdict, OrderedDict
from datetime import datetime
from math import ceil
# Use simplejson as it can deal with Decimal
import simplejson as json


# Calculate choropleth data, this needs to be done once as it is static
choropleth_dict = {}

models = {
    'United Nations': UN,
    'NATO': NATO,
    'World Bank': WorldBank
}

for model_name, model in models.items():
    model_choropleth_records = model.query.with_entities(
        model.year,
        model.amount,
        model.vendor_country,
        model.country_code
    ).all()
    model_choropleth_dict = defaultdict(dict)
    for line in model_choropleth_records:
        if line[3] not in model_choropleth_dict[line[0]]:
           model_choropleth_dict[line[0]][line[3]] = {
                'amount': line[1],
                'country_name': line[2]
            }
        else:
            model_choropleth_dict[line[0]][line[3]]['amount'] += line[1]

    choropleth_dict[model_name] = model_choropleth_dict

# Retrieve either the sum of the amounts or number of awarded contracts
# (len) per country
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
def create_choropleth_update(year, organisation):
    return {
        'data': [go.Choropleth(
            locations=list(choropleth_dict[organisation][year].keys()),
            z=[
                x['amount'] for x in list(
                    choropleth_dict[organisation][year].values()
                )
            ],
            text=[
                '{0}: ${1:,}'.format(x['country_name'], x['amount']) for x in list(
                    choropleth_dict[organisation][year].values()
                )
            ],
            hoverinfo="text",
        )],
        'layout': go.Layout(
            geo={
                'showframe': False,
                'projection': {'type': 'natural earth'},
                'showland': True,
                'landcolor': 'rgb(243, 243, 243)',
                'showocean': True,
                'oceancolor': 'steelblue',
            },
            margin=go.layout.Margin(
                l=55,
                r=55,
            ),
            font={
                'family': "'Montserrat', sans-serif"
            },
        )
    }


# Create the update for the Dash graph callback
def create_update(country, sum_or_len, numbers_or_percentages, organisation):
    y_axis_title = 'amount ($)'
    if sum_or_len == 'len':
        y_axis_title = 'number of awarded contracts'

    # Retrieve values
    country_values_dict = get_values(country, organisation, sum_or_len)
    if numbers_or_percentages == 'percentages':
        y_axis_title = 'percent (%)'
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
                'title': y_axis_title,
                'rangemode': "tozero",
                'hoverformat': "$,.2f"
            },
            title=organisation,
            font={
                'family': "'Montserrat', sans-serif"
            },
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
dash_app.css.append_css({"external_url": "/static/dash.css"})
dash_app.layout = html.Div(
    children=[
        html.H1('Show the data on a map'),
        dcc.Tabs(id="tabs", value='tab-un', children=[
            dcc.Tab(label='United Nations', value='tab-un'),
            dcc.Tab(label='NATO', value='tab-nato'),
            dcc.Tab(label='World Bank', value='tab-wb'),
        ]),
        html.Div(id='tabs-content'),

        html.Br(),

        html.H1('Compare the data per country'),
        html.Div([
            html.P(
                'Select country:',
            ),
            html.Div(
                [
                    dcc.Dropdown(
                        id='country',
                        options=unique_countries,
                        value='Netherlands'
                    )
                ],
            ),
        ]),
        html.Div([
            html.P(
                'Show:',
                style={'margin-bottom': '0'},
            ),
            html.Div([
                dcc.Dropdown(
                    id='sum_or_len',
                    options=[
                        {'label': 'total amount', 'value': 'sum'},
                        {
                            'label': 'number of awarded contracts',
                            'value': 'len'
                        }
                    ],
                    value='sum'
                )
            ]),
        ]),
        html.Div([
            html.P(
                'Format:',
                style={'margin-bottom': '0'},
            ),
            html.Div(
                [
                    dcc.Dropdown(
                        id='numbers_or_percentages',
                        options=[
                            {'label': 'numbers', 'value': 'numbers'},
                            {'label': 'percentages', 'value': 'percentages'}
                        ],
                        value='numbers'
                    )
                ],
            ),
        ]),

        html.Div(
            dcc.Graph(
                id='un',
                config={
                    'modeBarButtonsToRemove': [
                        'select2d', 'lasso2d', 'autoScale2d'
                    ]
                },
            ),
            className="four columns"
        ),
        html.Div(
            dcc.Graph(
                id='nato',
                config={
                    'modeBarButtonsToRemove': [
                        'select2d', 'lasso2d', 'autoScale2d'
                    ]
                },
            ),
            className="four columns"
        ),
        html.Div(
            dcc.Graph(
                id='world_bank',
                config={
                    'modeBarButtonsToRemove': [
                        'select2d', 'lasso2d', 'autoScale2d'
                    ]
                },
            ),
            className="four columns"
        ),
    ],
    style={'font-family': "'Montserrat', sans-serif"},
)

# Update tabs
@dash_app.callback(
    dash.dependencies.Output('tabs-content', 'children'),
    [dash.dependencies.Input('tabs', 'value')]
)
def render_content(tab):
    if tab == 'tab-un':
        return html.Div([
            html.Div([
                dcc.Graph(
                    id='un-choropleth',
                    config={
                        'modeBarButtonsToRemove': [
                            'select2d', 'lasso2d'
                        ]
                    },
                ),
            ]),
            html.Div(
                [
                    dcc.Slider(
                        id='un-slider',
                        min=2010,
                        max=2017,
                        value=2017,
                        marks={
                            2010: 2010,
                            2011: 2011,
                            2012: 2012,
                            2013: 2014,
                            2014: 2014,
                            2015: 2015,
                            2016: 2016,
                            2017: 2017
                        },
                    ),
                ],
                style={
                    'margin-left': '15',
                    'margin-right': '60',
                    'margin-bottom': '40'
                },
            ),
        ])
    elif tab == 'tab-nato':
        return html.Div([
            html.Div([
                dcc.Graph(
                    id='nato-choropleth',
                    config={
                        'modeBarButtonsToRemove': [
                            'select2d', 'lasso2d'
                        ]
                    },
                ),
            ]),
            html.Div(
                [
                    dcc.Slider(
                        id='nato-slider',
                        min=2009,
                        max=2018,
                        value=2018,
                        marks={
                            2009: 2009,
                            2010: 2010,
                            2011: 2011,
                            2012: 2012,
                            2013: 2014,
                            2014: 2014,
                            2015: 2015,
                            2016: 2016,
                            2017: 2017,
                            2018: 2018
                        },
                    ),
                ],
                style={
                    'margin-left': '15',
                    'margin-right': '58',
                    'margin-bottom': '40'
                },
            ),
        ])
    elif tab == 'tab-wb':
        return html.Div([
            html.Div([
                dcc.Graph(
                    id='wb-choropleth',
                    config={
                        'modeBarButtonsToRemove': [
                            'select2d', 'lasso2d'
                        ]
                    },
                ),
            ]),
            html.Div(
                [
                    dcc.Slider(
                        id='wb-slider',
                        min=2004,
                        max=2018,
                        value=2018,
                        marks={
                            2004: 2004,
                            2005: 2005,
                            2006: 2006,
                            2007: 2007,
                            2008: 2008,
                            2009: 2009,
                            2010: 2010,
                            2011: 2011,
                            2012: 2012,
                            2013: 2014,
                            2014: 2014,
                            2015: 2015,
                            2016: 2016,
                            2017: 2017,
                            2018: 2018
                        },
                    ),
                ],
                style={
                    'margin-left': '15',
                    'margin-right': '58',
                    'margin-bottom': '40'
                },
            ),
        ])


# Update callback for UN choropleth graph
@dash_app.callback(
    dash.dependencies.Output('un-choropleth', 'figure'),
    [
        dash.dependencies.Input('un-slider', 'value')
    ]
)
def update_graph(year):
    return create_choropleth_update(year, 'United Nations')


# Update callback for NATO choropleth graph
@dash_app.callback(
    dash.dependencies.Output('nato-choropleth', 'figure'),
    [
        dash.dependencies.Input('nato-slider', 'value')
    ]
)
def update_graph(year):
    return create_choropleth_update(year, 'NATO')


# Update callback for World Bank choropleth graph
@dash_app.callback(
    dash.dependencies.Output('wb-choropleth', 'figure'),
    [
        dash.dependencies.Input('wb-slider', 'value')
    ]
)
def update_graph(year):
    return create_choropleth_update(year, 'World Bank')


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
        ColumnDT(UN.amount),
        ColumnDT(UN.vendor_name),
        ColumnDT(UN.vendor_country),
        ColumnDT(UN.description),
        ColumnDT(UN.year),
        ColumnDT(UN.un_organisation),
        ColumnDT(UN.contracts_or_orders),
        ColumnDT(UN.number_of_contracts_or_orders)
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
        ColumnDT(NATO.amount),
        ColumnDT(NATO.vendor_name),
        ColumnDT(NATO.vendor_country),
        ColumnDT(NATO.description),
        ColumnDT(NATO.year),
        ColumnDT(NATO.type),
        ColumnDT(NATO.period)
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
        ColumnDT(WorldBank.amount),
        ColumnDT(WorldBank.vendor_name),
        ColumnDT(WorldBank.vendor_country),
        ColumnDT(WorldBank.description),
        ColumnDT(WorldBank.year),
        ColumnDT(WorldBank.commodity_category),
        ColumnDT(WorldBank.wbg_organization),
        ColumnDT(WorldBank.selection_number),
        ColumnDT(WorldBank.supplier_country_code),
        ColumnDT(WorldBank.fund_source),
        ColumnDT(WorldBank.vpu_description),
        ColumnDT(WorldBank.region),
        ColumnDT(WorldBank.borrower_country),
        ColumnDT(WorldBank.borrower_country_code),
        ColumnDT(WorldBank.project_id),
        ColumnDT(WorldBank.project_name),
        ColumnDT(WorldBank.procurement_type),
        ColumnDT(WorldBank.procurement_category),
        ColumnDT(WorldBank.procurement_method),
        ColumnDT(WorldBank.product_line),
        ColumnDT(WorldBank.major_sector),
        ColumnDT(WorldBank.wb_contract_number),
        ColumnDT(WorldBank.borrower_contract_reference_number),
        ColumnDT(WorldBank.contract_award_type)
    ]

    # Defining the initial query
    query = db.session.query().select_from(WorldBank)

    # Retrieve the GET parameters coming from the user
    params = request.args.to_dict()

    # Instantiate a DataTable for the query and table needed
    rowTable = DataTables(params, query, columns)

    # Convert datetime values to string
    output_result = rowTable.output_result()
    for row in output_result['data']:
            if type(row['5']) == datetime:
                row['5'] = row['5'].isoformat()[:10]
            if type(row['23']) == datetime:
                row['23'] = row['23'].isoformat()[:10]

    # returns what is needed by DataTable
    return json.dumps(output_result)


@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/data")
def data():
    return render_template('data.html')


if __name__ == "__main__":
    app.run(threaded=True)
