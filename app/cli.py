from app import app, db
from app.models import User, ckan, Election
from app.email import send_invite, send_mailcorrectie
from datetime import datetime
from flask import url_for
from pprint import pprint
import click
import copy
import json
import os
import uuid


# CKAN (use uppercase to avoid conflict with 'ckan' import from
# app.models)
@app.cli.group()
def CKAN():
    """ckan commands"""
    pass


@CKAN.command()
def toon_verkiezingen():
    """
    Toon alle huidige verkiezingen en de bijbehornde public en draft
    resources
    """
    pprint(ckan.elections)


@CKAN.command()
@click.argument('resource_id')
def maak_nieuwe_datastore(resource_id):
    """
    Maak een nieuwe datastore tabel in een resource
    """
    fields = [
        {
            "id": "Gemeente",
            "type": "text"
        },
        {
            "id": "CBS gemeentecode",
            "type": "text"
        },
        {
            "id": "Nummer stembureau",
            "type": "int"
        },
        {
            "id": "Naam stembureau",
            "type": "text"
        },
        {
            "id": "Gebruikersdoel het gebouw",
            "type": "text"
        },
        {
            "id": "Website locatie",
            "type": "text"
        },
        {
            "id": "Wijknaam",
            "type": "text"
        },
        {
            "id": "CBS wijknummer",
            "type": "text"
        },
        {
            "id": "Buurtnaam",
            "type": "text"
        },
        {
            "id": "CBS buurtnummer",
            "type": "text"
        },
        {
            "id": "BAG referentienummer",
            "type": "text"
        },
        {
            "id": "Straatnaam",
            "type": "text"
        },
        {
            "id": "Huisnummer",
            "type": "text"
        },
        {
            "id": "Huisnummertoevoeging",
            "type": "text"
        },
        {
            "id": "Postcode",
            "type": "text"
        },
        {
            "id": "Plaats",
            "type": "text"
        },
        {
            "id": "Extra adresaanduiding",
            "type": "text"
        },
        {
            "id": "X",
            "type": "int"
        },
        {
            "id": "Y",
            "type": "int"
        },
        {
            "id": "Longitude",
            "type": "float"
        },
        {
            "id": "Latitude",
            "type": "float"
        },
        {
            "id": "Districtcode",
            "type": "text"
        },
        {
            "id": "Openingstijden",
            "type": "text"
        },
        {
            "id": "Mindervaliden toegankelijk",
            "type": "text"
        },
        {
            "id": "Invalidenparkeerplaatsen",
            "type": "text"
        },
        {
            "id": "Akoestiek",
            "type": "text"
        },
        {
            "id": "Mindervalide toilet aanwezig",
            "type": "text"
        },
        {
            "id": "Kieskring ID",
            "type": "text"
        },
        {
            "id": "Hoofdstembureau",
            "type": "text"
        },
        {
            "id": "Contactgegevens",
            "type": "text"
        },
        {
            "id": "Beschikbaarheid",
            "type": "text"
        },
        {
            "id": "ID",
            "type": "text"
        },
        {
            "id": "UUID",
            "type": "text"
        }
    ]

    ckan.create_datastore(resource_id, fields)


@CKAN.command()
@click.argument('resource_id')
def export_resource(resource_id):
    """
    Exports all records of a resource to a json file in the exports directory
    """
    all_resource_records = ckan.get_records(resource_id)['records']
    filename = 'exports/%s_%s.json' % (
        datetime.now().isoformat()[:19],
        resource_id
    )
    with open(filename, 'w') as OUT:
        json.dump(all_resource_records, OUT, indent=4, sort_keys=True)


@CKAN.command()
@click.argument('resource_id')
@click.argument('file_path')
def import_resource(resource_id, file_path):
    """
    Import records to a resource from a json file
    """
    with open(file_path) as IN:
        records = json.load(IN)
        for record in records:
            if '_id' in record:
                del record['_id']
        ckan.save_records(resource_id, records)


@CKAN.command()
@click.pass_context
def add_uuid(ctx):
    """
    Add uuid
    """
    verkiezingen = [
        'Referendum over de Wet op de inlichtingen- en veiligheidsdiensten',
        'Gemeenteraadsverkiezingen 2018'
    ]

    # Retrieve all records and generate one UUID for the same records
    print('Retrieving...')
    all_records = {}
    for verkiezing in verkiezingen:
        for resource in ['draft_resource', 'publish_resource']:
            resource_id = ckan.elections[verkiezing][resource]
            all_resource_records = ckan.get_records(resource_id)['records']
            for record in all_resource_records:
                equal_fields_record = copy.deepcopy(record)
                _remove_differing_fields(equal_fields_record)
                found_in_all_records = False
                for uuid_str, value in all_records.items():
                    if value['equal_fields_record'] == equal_fields_record:
                        if not verkiezing in value['orig_records']:
                            value['orig_records'][verkiezing] = {}
                        value['orig_records'][verkiezing][resource_id] = record
                        found_in_all_records = True
                if not found_in_all_records:
                    new_uuid = uuid.uuid4().hex
                    all_records[new_uuid] = {
                        'equal_fields_record': equal_fields_record,
                        'orig_records': {
                            verkiezing: {
                                resource_id: record
                            }
                        }
                    }

    # Delete all records and add new datastore
    print('Deleting...')
    for verkiezing in verkiezingen:
        for resource in ['draft_resource', 'publish_resource']:
            resource_id = ckan.elections[verkiezing][resource]
            ckan.delete_records(resource_id)
            ctx.invoke(maak_nieuwe_datastore, resource_id=resource_id)

    # Save all records now with UUID
    print('Saving...')
    for uuid_str, value in all_records.items():
        for verkiezing, resource_ids in value['orig_records'].items():
            for resource_id, record in resource_ids.items():
                del record['_id']
                del record['primary_key']
                record['UUID'] = uuid_str
                ckan.save_records(
                    resource_id=resource_id,
                    records=[record]
                )


def _remove_differing_fields(record):
    del record['_id']
    del record['primary_key']
    del record['Kieskring ID']
    del record['Hoofdstembureau']
    del record['ID']


@CKAN.command()
@click.argument('resource_id')
def resource_show(resource_id):
    """
    Show datastore resource metadata
    """
    pprint(ckan.resource_show(resource_id))


@CKAN.command()
@click.argument('resource_id')
def test_upsert_datastore(resource_id):
    """
    Insert of update data in de datastore tabel in een resource met 1
    voorbeeld record als test
    """
    record = {
        "Gemeente": "'s-Gravenhage",
        "CBS gemeentecode": "GM0518",
        "Nummer stembureau": "517",
        "Naam stembureau": "Stadhuis",
        "Gebruikersdoel het gebouw": "kantoor",
        "Website locatie": (
            "https://www.denhaag.nl/nl/bestuur-en-organisatie/contact-met-"
            "de-gemeente/stadhuis-den-haag.htm"
        ),
        "Wijknaam": "Centrum",
        "CBS wijknummer": "WK051828",
        "Buurtnaam": "Kortenbos",
        "CBS buurtnummer": "BU05182811",
        "BAG referentienummer": "0518100000275247",
        "Straatnaam": "Spui",
        "Huisnummer": 70,
        "Huisnummertoevoeging": "",
        "Postcode": "2511 BT",
        "Plaats": "Den Haag",
        "Extra adresaanduiding": "",
        "X": 81611,
        "Y": 454909,
        "Longitude": 4.3166395,
        "Latitude": 52.0775912,
        "Openingstijden": "2017-03-21T07:30:00 tot 2017-03-21T21:00:00",
        "Mindervaliden toegankelijk": 'Y',
        "Invalidenparkeerplaatsen": 'N',
        "Akoestiek": 'Y',
        "Mindervalide toilet aanwezig": 'N',
        "Kieskring ID": "'s-Gravenhage",
        "Contactgegevens": "persoonx@denhaag.nl",
        "Beschikbaarheid": "https://www.stembureausindenhaag.nl/",
        "ID": "NLODSGM0518stembureaus20180321001",
        "UUID": uuid.uuid4().hex
    }
    ckan.save_records(
        resource_id=resource_id,
        records=[record]
    )


@CKAN.command()
@click.argument('resource_id')
def verwijder_datastore(resource_id):
    """
    Verwijder een datastore tabel in een resource
    """
    ckan.delete_datastore(resource_id)


# Gemeenten
@app.cli.group()
def gemeenten():
    """Gemeenten gerelateerde commands"""
    pass


@gemeenten.command()
def toon_alle_gemeenten():
    """
    Toon alle gemeenten en bijbehorende verkiezingen in de database
    """
    for user in User.query.all():
        print(
            '"%s","%s","%s",["%s"]' % (
                user.gemeente_naam,
                user.gemeente_code,
                user.email,
                ", ".join([x.verkiezing for x in user.elections.all()])
            )
        )


@gemeenten.command()
def verwijder_alle_gemeenten_en_verkiezingen():
    """
    Gebruik dit enkel in development. Deze command verwijdert alle
    gemeenten en verkiezingen uit de MySQL database.
    """
    if not app.debug:
        result = input(
            'Je voert deze command in PRODUCTIE uit. Weet je zeker dat je '
            'alle gemeenten en verkiezingen wilt verwijderen uit de MySQL '
            'database? (y/N): '
        )
        # Print empty line for better readability
        print()
        if not result.lower() == 'y':
            print("Geen gemeenten verwijderd")
            return

    total_removed = User.query.delete()
    print("%d gemeenten verwijderd" % total_removed)
    db.session.commit()


@gemeenten.command()
def eenmalig_gemeenten_en_verkiezingen_aanmaken():
    """
    Gebruik deze command slechts eenmaal(!) om alle gemeenten en
    verkiezingen in de database aan te maken op basis van
    'app/data/gemeenten.json'
    """
    if not app.debug:
        result = input(
            'Je voert deze command in PRODUCTIE uit. Weet je zeker dat je '
            'alle gemeenten en verkiezingen wilt aanmaken in de MySQL '
            'database? (y/N): '
        )
        # Print empty line for better readability
        print()
        if not result.lower() == 'y':
            print('Geen gemeenten en verkiezingen aangemaakt')
            return

    with open('app/data/gemeenten.json', newline='') as IN:
        data = json.load(IN)
        total_created = 0
        for item in data:
            user = User(
                gemeente_naam=item['gemeente_naam'],
                gemeente_code=item['gemeente_code'],
                email=item['email']
            )
            user.set_password(os.urandom(24))
            db.session.add(user)

            for verkiezing in item['verkiezingen']:
                election = Election(verkiezing=verkiezing, gemeente=user)

            total_created += 1
        # Only commit if all users are successfully added
        db.session.commit()
        print(
            '%d gemeenten (en bijbehorende verkiezingen) aangemaakt' % (
                total_created
            )
        )


@gemeenten.command()
def eenmalig_gemeenten_uitnodigen():
    """
    Gebruik deze command slechts eenmaal(!) om alle gemeenten, die je
    eerst hebt aangemaakt met 'gemeenten eenmalig_gemeenten_aanmaken',
    een e-mail te sturen met instructies en de vraag om een wachtwoord
    aan te maken
    """
    if not app.debug:
        result = input(
            'Je voert deze command in PRODUCTIE uit. Weet je zeker dat je '
            'alle gemeenten wilt uitnodigen voor waarismijnstemlokaal.nl en '
            'vragen om een wachtwoord aan te maken? (y/N): '
        )
        # Print empty line for better readability
        print()
        if not result.lower() == 'y':
            print('Geen gemeenten ge-e-maild')
            return

    total_mailed = 0
    for user in User.query.all():
        send_invite(user, 349725)
        total_mailed += 1
    print('%d gemeenten ge-e-maild' % (total_mailed))


@gemeenten.command()
@click.argument('gemeente_code')
def gemeente_invite_link_maken(gemeente_code):
    """
    Maak een reset wachtwoord link aan voor een gemeente. Handig om via een
    ander kanaal een gemeente haar wachtwoord te laten resetten. Geef de CBS
    gemeentecode mee als parameter (bv. GM1680).
    """
    user = User.query.filter_by(gemeente_code=gemeente_code).first()
    if not user:
        print('Gemeentecode "%s" staat niet in de database' % (gemeente_code))
        return
    token = user.get_reset_password_token()
    print(
        'Password reset link voor %s van gemeente %s (%s): %s' % (
            user.email,
            user.gemeente_code,
            user.gemeente_naam,
            url_for('gemeente_reset_wachtwoord', token=token, _external=True)
        )
    )


@gemeenten.command()
def eenmalig_gemeenten_mailcorrectie():
    if not app.debug:
        result = input(
            'Je voert deze command in PRODUCTIE uit. Weet je zeker dat je '
            'alle gemeenten wilt uitnodigen voor waarismijnstemlokaal.nl en '
            'vragen om een wachtwoord aan te maken? (y/N): '
        )
        # Print empty line for better readability
        print()
        if not result.lower() == 'y':
            print('Geen gemeenten ge-e-maild')
            return

    total_mailed = 0
    for user in User.query.all():
        send_mailcorrectie(user)
        total_mailed += 1
    print('%d gemeenten ge-e-maild' % (total_mailed))
