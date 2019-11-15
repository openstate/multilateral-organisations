#!/usr/bin/env python3

import csv
import re
import json

filename = 'Major_Contract_Awards.csv'

data = []

with open('../normalize_countries.json') as IN:
    countries = json.load(IN)

with open('../country_codes.json') as IN:
    country_codes = json.load(IN)

with open(filename) as IN:
    reader = csv.reader(IN)

    current_org = 'World Bank'

    #column_order = [6, 1, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 5, 18, 3, 2, 19, 4, 20]
    #column_order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    column_order = [1, 16, 15, 18, 13, 21, 0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 17, 19]

    # Skip headers
    next(reader)

    for row in reader:
        # Normalize country name
        if row[16] in countries:
            row[16] = countries[row[16]]

        # Add country code
        row.append(country_codes.get(row[16], ''))

        data.append([current_org] + [row[x] for x in column_order] + ['Major Contract Award'])

column_names = [
    'organisation',
    'year',
    'vendor_country',
    'vendor_name',
    'amount',
    'description',
    'country_code'
]

# Commented names are replaced with the standardized names from
# the `column_names` list
extra_column_names = [
    'As of Date',
    #'Fiscal Year',
    'Region',
    'Borrower Country',
    'Borrower Country Code',
    'Project ID',
    'Project Name',
    'Procurement Type',
    'Procurement Category',
    'Procurement Method',
    'Product line',
    'Major Sector',
    'WB Contract Number',
    #'Contract Description',
    'Contract Signing Date',
    #'Supplier',
    #'Supplier Country',
    'Supplier Country Code',
    #'Total Contract Amount (USD)',
    'Borrower Contract Reference Number',
    'Contract Award Type'
]

with open('../../files/World_Bank_major_contract_awards.csv', 'w') as OUT:
    writer = csv.writer(OUT)
    writer.writerow(column_names + extra_column_names)
    writer.writerows(sorted(data))
