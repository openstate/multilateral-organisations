#!/usr/bin/env python3

import csv
import re
import json

filename = 'Corporate_Procurement_Contract_Awards.csv'

data = []

with open('../normalize_countries.json') as IN:
    countries = json.load(IN)

with open('../country_codes.json') as IN:
    country_codes = json.load(IN)

with open(filename) as IN:
    reader = csv.reader(IN)

    current_org = 'World Bank'

    column_order = [1, 7, 6, 9, 3, 12, 0, 2, 4, 5, 8, 10, 11]

    # Skip headers
    next(reader)

    for row in reader:
        # Normalize country name
        if row[7] in countries:
            row[7] = countries[row[7]]

        # Add country code
        row.append(country_codes.get(row[7], ''))

        row[1] = '20' + row[1][-2:]
        data.append([current_org] + [row[x] for x in column_order] + ['Corporate Procurement Contract Award'])

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
    'Award Date',
    #'Quarter and Fiscal Year',
    'Commodity Category',
    #'Contract Description',
    'WBG Organization',
    'Selection Number',
    #'Supplier',
    #'Supplier Country',
    'Supplier Country Code',
    #'Contract Award Amount',
    'Fund Source',
    'VPU description',
    'Contract Award Type'
]

with open('../../files/World_Bank_corporate_procurement_contract_awards.csv', 'w') as OUT:
    writer = csv.writer(OUT)
    writer.writerow(column_names + extra_column_names)
    writer.writerows(sorted(data))
