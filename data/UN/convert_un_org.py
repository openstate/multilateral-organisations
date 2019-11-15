#!/usr/bin/env python3

import csv
import json
import re

with open('../normalize_countries.json') as IN:
    countries = json.load(IN)

with open('../normalize_un.json') as IN:
    un = json.load(IN)

with open('../country_codes.json') as IN:
    country_codes = json.load(IN)

# Since 2018 the data is published as spreadsheet so demark that and
# later years with 'xls'
# 'new' years have only one type of data per year
# 'old' years have 'contracts' and 'orders' data per year
years = {
    '2018': 'xls',
    '2017': 'new',
    '2016': 'new',
    '2015': 'new',
    '2014': 'old',
    '2013': 'old',
    '2012': 'old',
    '2011': 'old',
    '2010': 'old'
}

# Set these amounts to none
skip_list = [
    '###########',
    '-'
]

# 2012_contracts.pdf and 2014_orders.pdf contain description columns
# that run over into the amount columns, resulting in some messy
# amounts. Most can be cleaned automatically, but some need a manual
# mapping.
replace_list = {
    '0c32390.00': '32390.00',
    '1D37800.00': '37800.00',
    '1p0p0lie0s00.00': '100000.00',
    '1s1500000.00': '11500000.00',
    '1u1p3p5lie7s38.56': '1135738.56',
    '2/34820.00': ' 34820.00',
    '2e0s5781.39': '205781.39',
    '2F68130.00': '268130.00',
    '2n3f5190.00': '35190.00',
    '2p5p0lie0s00.00': '250000.00',
    '3A41980.00': '41980.00',
    '3u5p0p0lie0s00.00': '3500000.00',
    '4p0p0lie0s00.00': '400000.00',
    '4u0p0p0lie0s00.00': '4000000.00',
    '5p0lie0s00.00': '50000.00',
    '5p0p0lie0s00.00': '500000.00',
    '5s3607.72': '53607.72',
    '5s9258.36': '59258.36',
    '6p0p0lie0s00.00': '600000',
    '6x41140.00': '41140.00',
    '7p0lie0s00.00': '70000.00',
    '7p0p0lie0s00.00': '700000.00',
    '8s6769.35': '86769.35',
    '9p0p0lie0s00.00': '900000.00',
    '183d3a1t800.00': '31800.00',
    '5Y50000.00': '50000.00'
}

data = []

for year, year_type in years.items():
    filename_base = year

    year_type_strings = ['']
    if year_type == 'old':
        year_type_strings = [
            '_contracts',
            '_orders'
        ]

    for year_type_string in year_type_strings:
        with open(filename_base + year_type_string + '_raw.csv') as IN:
            reader = csv.reader(IN)
        
            current_org = 'UN'
            current_un_org = ''
        
            for row in reader:
                # The raw data from 2017 and earlier list the UN
                # organisation only once at the top of a section, this
                # block retrieves that; otherwise simply get it from the
                # row (i.e. for 2018 and later data)
                if (row[0] != '' and row[1] == ''
                        and row[2] == '' and row[3] == ''):
                    current_un_org = row[0].strip(' continued')
                    current_un_org = re.sub(
                        ' continued', '', row[0], flags=re.I
                    )
                    # Normalize UN organization name
                    current_un_org = un[current_un_org]
                    continue
                elif year_type == 'xls':
                    current_un_org = row[1]
                    # Normalize UN organization name
                    current_un_org = un[current_un_org]
        
                # Skip rows which don't have values in all columns
                if '' in row:
                    continue
        
                if year_type == 'xls':
                    # Companies with comma's in their name have
                    # unnecessary quotation marks, so remove them
                    if (row[3].startswith('"')
                            and row[3].endswith('"') and ',' in row[3]):
                        row[3] = row[3][1:-1]
                    new_record = [current_org] + [year] + row[2:4]
                else:
                    new_record = [current_org] + [year] + row[0:2]

                # Normalize country name
                if new_record[2] in countries:
                    new_record[2] = countries[new_record[2]]
                else:
                    exit(
                        'COULD NOT FIND COUNTRY IN COUNTRIES LIST: %s' % (
                            new_record[2]
                        )
                    )

                # Add country code
                country_code = country_codes.get(new_record[2], '')

                # The 2013 data contains a order/contract # column, so remove
                # the thousand separator from row[4] instead of row[3] and
                # append the columns in the right order to data.
                # The 'xls' years have a different structure as well.
                if year == '2013':
                    if row[4] in skip_list:
                        row[4] = ''
                    row[4] = re.sub('^[a-zA-Z/.]*', '', row[4])
                    row[4] = row[4].replace(',', '').replace(' ', '')
                    if row[4] in replace_list:
                        row[4] = replace_list[row[4]]
                    # Remove this line below the table in 2013
                    if 'name of the contractor is not displayed when it includes the name of an individual' in row:
                        continue
                    data.append(new_record + [row[4], row[2], country_code, current_un_org, year_type_string[1:], row[3]])
                elif year_type == 'xls':
                    row[5] = row[5].replace(',', '').replace(' ', '')
                    if row[5] in skip_list:
                        row[5] = ''
                    data.append(new_record + [row[5], row[4], country_code, current_un_org])
                else:
                    if row[3] in skip_list:
                        row[3] = ''
                    row[3] = re.sub('^[a-zA-Z/. ]*', '', row[3])
                    row[3] = row[3].replace(',', '').replace(' ', '')
                    if row[3] in replace_list:
                        row[3] = replace_list[row[3]]
                    data.append(new_record + [row[3], row[2], country_code, current_un_org, year_type_string[1:]])
        
column_names = [
    'organisation',
    'year',
    'vendor_country',
    'vendor_name',
    'amount',
    'description',
    'country_code'
]

extra_column_names = [
    'un_organisation',
    'contracts_or_orders',
    'number_of_contracts_or_orders'
]

with open('../../files/UN.csv', 'w') as OUT:
    writer = csv.writer(OUT)
    writer.writerow(column_names + extra_column_names)
    writer.writerows(sorted(data))
