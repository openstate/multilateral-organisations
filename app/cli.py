from app import app, db
from app.models import UN, NATO, WorldBank
from datetime import datetime
from decimal import Decimal
import click
import csv
import re


# MLO
@app.cli.group()
def MLO():
    """open multilaterals commands"""
    pass

@MLO.command()
@click.option('--csv-file', default='')
def load_records(csv_file):
    """
    Add records to the database. NOTE: records are added even if
    they already exist, so only use this when loading the records for
    the first time or when adding new records
    """

    if csv_file == '':
        print(
            'Please give a --csv-file argument, e.g. files/NATO.csv'
        )
        exit()

    total_created = 0

    with open(csv_file) as IN:
        reader = csv.DictReader(IN)
        for record in reader:
            if record['organisation'] == 'UN':
                new_record = UN(
                    organisation=record['organisation'],
                    year=int(record['year']),
                    vendor_country=record['vendor_country'],
                    vendor_name=record['vendor_name'],
                    amount=(
                        Decimal(record['amount']) if re.match(
                            '^\d+\.?\d+$', record['amount']
                        ) else 0
                    ),
                    description=record['description'],
                    un_organisation=record['un_organisation'],
                    contracts_or_orders=record['contracts_or_orders'],
                    number_of_contracts_or_orders=record[
                        'number_of_contracts_or_orders'
                    ]
                )
            elif record['organisation'] == 'NATO':
                new_record = NATO(
                    organisation=record['organisation'],
                    year=int(record['year']),
                    vendor_country=record['vendor_country'],
                    vendor_name=record['vendor_name'],
                    amount=Decimal(record['amount']),
                    description=record['description'],
                    type=record['Type'],
                    period=record['Period'],
                )
            # The WorldBank table can combine data from Major Contract
            # Awards and Corporate Procurement Contract Awards, that is
            # why we need to check if a field is present as these two
            # datasets have several different fields
            elif (record['organisation'] == 'World Bank'):
                if not 'Contract Signing Date' in record:
                    contract_signing_date = None
                else:
                    contract_signing_date = datetime.strptime(
                        record['Contract Signing Date'], '%m/%d/%Y %I:%M:%S %p'
                    ) if record['Contract Signing Date'] else None,
                new_record = WorldBank(
                    organisation=record['organisation'],
                    year=int(record['year']),
                    vendor_country=record['vendor_country'],
                    vendor_name=record['vendor_name'],
                    amount=(
                        Decimal(record['amount']) if record['amount'] else 0
                    ),
                    description=record['description'],
                    award_date=datetime.strptime(
                        record['Award Date'], '%m/%d/%Y %I:%M:%S %p'
                    ) if 'Award Date' in record else None,
                    commodity_category=record['Commodity Category'] if 'Commodity Category' in record else '',
                    wbg_organization=record['WBG Organization'] if 'WBG Organization' in record else '',
                    selection_number=record['Selection Number'] if 'Selection Number' in record else '',
                    supplier_country_code=record['Supplier Country Code'] if 'Supplier Country Code' in record else '',
                    fund_source=record['Fund Source'] if 'Fund Source' in record else '',
                    vpu_description=record['VPU description'] if 'VPU description' in record else '',
                    region=record['Region'] if 'Region' in record else '',
                    borrower_country=record['Borrower Country'] if 'Borrower Country' in record else '',
                    borrower_country_code=record['Borrower Country Code'] if 'Borrower Country Code' in record else '',
                    project_id=record['Project ID'] if 'Project ID' in record else '',
                    project_name=record['Project Name'] if 'Project Name' in record else '',
                    procurement_type=record['Procurement Type'] if 'Procurement Type' in record else '',
                    procurement_category=record['Procurement Category'] if 'Procurement Category' in record else '',
                    procurement_method=record['Procurement Method'] if 'Procurement Method' in record else '',
                    product_line=record['Product line'] if 'Product line' in record else '',
                    major_sector=record['Major Sector'] if 'Major Sector' in record else '',
                    wb_contract_number=record['WB Contract Number'] if 'WB Contract Number' in record else 0,
                    contract_signing_date=contract_signing_date,
                    borrower_contract_reference_number=record[
                        'Borrower Contract Reference Number'
                    ] if 'Borrower Contract Reference Number' in record else '',
                    contract_award_type=record['Contract Award Type']
                )

            if new_record:
                db.session.add(new_record)

                total_created += 1

    # Only commit if all records are successfully added
    db.session.commit()

    print(
        '%d records added to database' % (
            total_created
        )
    )


@MLO.command()
@click.option('--organisation', default='')
def show_records(organisation):
    """
    Show all records for a certain organisation, either 'UN', 'NATO' or
    'World Bank'
    """
    if organisation == '':
        print(
            "Pass an organisation to the --organisation argument: either "
            "'UN', 'NATO' or 'World Bank'"
        )
        exit()
    elif organisation == 'UN':
        print('Showing records for UN:')
        for record in UN.query.all():
            data = vars(record)
            data.pop('_sa_instance_state')
            print(data.values())
    elif organisation == 'NATO':
        print('Showing records for NATO:')
        for record in NATO.query.all():
            data = vars(record)
            data.pop('_sa_instance_state')
            print(data.values())
    elif organisation == 'World Bank':
        print('Showing records for World Bank:')
        for record in WorldBank.query.all():
            data = vars(record)
            data.pop('_sa_instance_state')
            print(data.values())


@MLO.command()
@click.option('--organisation', default='')
def remove_all_records(organisation):
    """
    Use this only in development! this command removes all records from
    the specified organisation from the MySQL database.
    """
    if organisation == '':
        print(
            "Pass an organisation to the --organisation argument: either "
            "'UN', 'NATO' or 'World Bank'"
        )
        exit()

    if not app.debug:
        result = input(
            'You are running this command in PRODUCTION. Are you sure that '
            'you want to remove all records for "%s" from the MySQL '
            'database? (y/N): ' % (organisation)
        )
        # Print empty line for better readability
        print()
        if not result.lower() == 'y':
            print("No records removed")
            return

    if organisation == 'UN':
        total_removed = UN.query.delete()
        print("%d UN records removed" % total_removed)
        db.session.commit()
    elif organisation == 'NATO':
        total_removed = NATO.query.delete()
        print("%d NATO records removed" % total_removed)
        db.session.commit()
    elif organisation == 'World Bank':
        total_removed = WorldBank.query.delete()
        print("%d World Bank records removed" % total_removed)
        db.session.commit()
