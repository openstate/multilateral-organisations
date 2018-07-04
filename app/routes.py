import csv
import os
import sys

from flask import render_template, request, redirect, url_for, flash, Markup
from sqlalchemy.sql import func

from app import app, db
from app.forms import SelectionForm
from app.models import NATO

from collections import defaultdict
from math import ceil


# Retrieve either the sum of the amounts or number of transactions (len)
# per country
def get_values(country, value_type='sum'):
    # If country is 'all' retrieve data of all countries
    if country == 'all':
        nato_country_records = NATO.query.with_entities(NATO.year, NATO.amount).all()
    else:
        nato_country_records = NATO.query.filter_by(vendor_country=country).with_entities(NATO.year, NATO.amount).all()

    nato_records_dict = defaultdict(list)
    for record in nato_country_records:
        nato_records_dict[record[0]].append(record[1])

    nato_values_dict = {}
    for year, amounts in nato_records_dict.items():
        if value_type == 'sum':
            nato_values_dict[year] = sum(amounts)
        elif value_type == 'len':
            nato_values_dict[year] = len(amounts)

    return nato_values_dict


@app.route("/", methods=['GET', 'POST'])
def index():
    selection_form = SelectionForm()

    # Create selection form
    unique_countries = NATO.query.with_entities(NATO.vendor_country).distinct().all()
    selection_form.country.choices = [(x[0], x[0]) for x in unique_countries]

    # Set default selections or retrieve selections from user
    selected_country = 'Netherlands'
    value_type = 'sum'
    num_or_perc = 'numbers'
    if selection_form.validate_on_submit():
        selected_country = selection_form.country.data
        value_type = selection_form.value_type.data
        num_or_perc = selection_form.num_or_perc.data

    # Set form fields defaults to specified selections
    selection_form.country.default = selected_country
    selection_form.value_type.default = value_type
    selection_form.num_or_perc.default = num_or_perc
    selection_form.process()

    # Retrieve values
    nato_all_values_dict = get_values('all', value_type)
    nato_country_values_dict = get_values(selected_country, value_type)

    # Calculate percentages if needed
    if num_or_perc == 'percentages':
        for year, amount in nato_country_values_dict.items():
            nato_country_values_dict[year] = amount / nato_all_values_dict[year] * 100

    return render_template(
        'index.html',
        selection_form=selection_form,
        nato_country_values_dict=nato_country_values_dict
    )


@app.route("/over-deze-website")
def over_deze_website():
    return render_template('over-deze-website.html')


@app.route("/data")
def data():
    return render_template('data.html')


# form + pagination
@app.route("/gemeente-stemlokalen-overzicht", methods=['GET', 'POST'])
def gemeente_stemlokalen_overzicht():
    # Pagination
    posts_per_page = app.config['POSTS_PER_PAGE']
    page = request.args.get('page', 1, type=int)

    # Use page 1 if a page lower than 1 is requested
    if page < 1:
        page = 1

    # If the user requests a page larger than the largest page for which
    # we have records to show, use that page instead of the requested
    # one
    if page > ceil(len(gemeente_draft_records) / posts_per_page):
        page = ceil(len(gemeente_draft_records) / posts_per_page)

    start_record = (page - 1) * posts_per_page
    end_record = page * posts_per_page
    if end_record > len(gemeente_draft_records):
        end_record = len(gemeente_draft_records)
    paged_draft_records = gemeente_draft_records[start_record:end_record]

    previous_url = None
    if page > 1:
        previous_url = url_for(
            'gemeente_stemlokalen_overzicht',
            page=page - 1
        )
    next_url = None
    if len(gemeente_draft_records) > page * posts_per_page:
        next_url = url_for(
            'gemeente_stemlokalen_overzicht',
            page=page + 1
        )

    return render_template(
        'gemeente-stemlokalen-overzicht.html',
        page=page,
        start_record=start_record + 1,
        end_record=end_record,
        total_records=len(gemeente_draft_records),
        total_pages=ceil(len(gemeente_draft_records)/posts_per_page),
        previous_url=previous_url,
        next_url=next_url
    )


if __name__ == "__main__":
    app.run(threaded=True)
