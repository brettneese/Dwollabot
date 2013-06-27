from app import db

class User(db.Model):
    id = db.Column(db.Integer)
    phone = db.Column(db.String(11), primary_key = True)
    token = db.Column(db.String(120))
    email = db.Column(db.String(120), index = True, unique = True)
    dwolla_id = db.Column(db.String(12))

    def __repr__(self):
        return '<User %r>' % (self.token)