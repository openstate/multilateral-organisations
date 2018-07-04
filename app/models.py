from app import app, db


class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    organisation = db.Column(db.String(32), index=True)
    year = db.Column(db.Integer, index=True)
    vendor_country = db.Column(db.String(64), index=True)
    vendor_name = db.Column(db.String(128), index=True)
    amount = db.Column(db.Float)
    description = db.Column(db.Text, index=True)

# NATO data
class NATO(Base):
    type = db.Column(db.String(24), index=True)
    period = db.Column(db.String(4), index=True)

# Create the tables above if they don't exist
db.create_all()
