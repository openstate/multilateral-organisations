from app import app, db


class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    organisation = db.Column(db.String(16), index=True)
    year = db.Column(db.Integer, index=True)
    vendor_country = db.Column(db.String(64), index=True)
    vendor_name = db.Column(db.String(256), index=True)
    amount = db.Column(db.Numeric(13, 2))
    description = db.Column(db.Text)
    country_code = db.Column(db.String(3), index=True)


# UN data
class UN(Base):
    un_organisation = db.Column(db.String(32), index=True)
    contracts_or_orders = db.Column(db.String(12), index=True)
    number_of_contracts_or_orders = db.Column(db.Integer)


# NATO data
class NATO(Base):
    type = db.Column(db.String(24), index=True)
    period = db.Column(db.String(4), index=True)


## World Bank data
# Combines data coming from Major Contract Awards and Corporate
# Procurement Contract Award
class WorldBank(Base):
    award_date = db.Column(db.DateTime, index=True, nullable=True)
    commodity_category = db.Column(db.String(64), index=True)
    wbg_organization = db.Column(db.String(12), index=True)
    selection_number = db.Column(db.String(96), index=True)
    supplier_country_code = db.Column(db.String(3), index=True)
    fund_source = db.Column(db.String(32), index=True)
    vpu_description = db.Column(db.String(96), index=True)
    region = db.Column(db.String(64), index=True)
    borrower_country = db.Column(db.String(64), index=True)
    borrower_country_code = db.Column(db.String(2), index=True)
    project_id = db.Column(db.String(8), index=True)
    project_name = db.Column(db.String(64), index=True)
    procurement_type = db.Column(db.String(64), index=True)
    procurement_category = db.Column(db.String(32), index=True)
    procurement_method = db.Column(db.String(64), index=True)
    product_line = db.Column(db.String(64), index=True)
    major_sector = db.Column(db.String(32), index=True)
    wb_contract_number = db.Column(db.Integer, index=True)
    contract_signing_date = db.Column(db.DateTime, index=True, nullable=True)
    borrower_contract_reference_number = db.Column(db.String(96), index=True)
    contract_award_type = db.Column(db.String(36), index=True)


# Create the tables above if they don't exist
db.create_all()
