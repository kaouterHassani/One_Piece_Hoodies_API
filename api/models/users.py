from ..utils import db
from datetime import datetime

class User(db.Model):
    ##name of the table
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    userName = db.Column(db.String(50), nullable=False)
    Email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.Text(), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='CLIENT')  # New field for user role
    is_staff = db.Column(db.Boolean(), default=False)
    is_active = db.Column(db.Boolean(), default=False)
    date_created = db.Column(db.DateTime(), default=datetime.utcnow)
    #relationship
    order = db.relationship('Order', backref="user_order", lazy=True)




    def __repr__(self):
        return f"<User {self.userName}>"
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    @classmethod
    def get_by_id(cls,id):
        return cls.query.get_or_404(id)


    def delete(self):
        db.session.delete(self)
        db.session.commit()
    