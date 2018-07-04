from app import app, db
from app.models import NATO
import click
import csv


# MLO
@app.cli.group()
def MLO():
    """multilaterale organisatie commands"""
    pass

@MLO.command()
@click.option('--csv-file', default='app/data/NAVO-BIDDING-PROC-COMBI.csv')
def load_data(csv_file):
    """
    Add NATO records to the database. NOTE: records are added even if
    they already exist, so only use this when loading the records for
    the first time or when adding new records
    """
    total_created = 0

    with open(csv_file) as IN:
        #TODO as dict
        reader = csv.DictReader(IN)
        for record in reader:
            nato = NATO(
                organisation=record['organisation'],
                year=int(record['year']),
                vendor_country=record['vendor_country'],
                vendor_name=record['vendor_name'],
                amount=float(record['amount']),
                description=record['description'],
                type=record['Type'],
                period=record['Period'],
            )
            db.session.add(nato)

            # Only commit if all records are successfully added
            db.session.commit()

            total_created += 1

    print(
        '%d NATO records added to database' % (
            total_created
        )
    )


@MLO.command()
@click.option('--organisation', default='NATO')
def show_records(organisation):
    """
    Show all records for a certain organisation
    """
    if organisation == 'NATO':
        for record in NATO.query.all():
            print(
                '"%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
                    record.id,
                    record.organisation,
                    record.year,
                    record.vendor_country,
                    record.vendor_name,
                    record.amount,
                    record.description,
                    record.type,
                    record.period
                )
            )


@MLO.command()
@click.option('--organisation', default='NATO')
def remove_all_records(organisation):
    """
    Use this only in development! this command removes all records from
    the specified organisation from the MySQL database.
    """
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

    if organisation == 'NATO':
        total_removed = NATO.query.delete()
        print("%d NATO records removed" % total_removed)
        db.session.commit()
