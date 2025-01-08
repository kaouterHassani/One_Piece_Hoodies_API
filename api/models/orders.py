from ..utils import db
from enum import Enum
from datetime import datetime


class Sizes(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"


class Colors(Enum):
    RED = "red"
    BLUE = "blue"
    BLACK = "black"
    WHITE = "white"
    PINK = "pink"
    PURPLE = "purple"
    GREEN = "green"

class PrintDesigns(Enum):
    STRAW_HAT_JOLLY_ROGER = "Straw Hat Jolly Roger"
    RORONOA_ZORO_SWORDS = "Roronoa Zoro's Swords"
    GOING_MERRY = "Going Merry"
    THOUSAND_SUNNY = "Thousand Sunny"
    MONKEY_D_LUFFY = "Monkey D. Luffy"
    PIRATE_KING = "Pirate King Logo"
    WANTED_POSTER = "Wanted Poster Design"

class Materials(Enum):
    COTTON = "cotton"
    POLYSTER ="polyster"
    MIXED = "mixed"

class OrderStatus(Enum):
    PENDING = "Pending"  # Order placed but not processed yet
    IN_PROGRESS = "In Progress"  # Order is being prepared (e.g., printing the T-shirt)
    SHIPPED = "Shipped"  # Order has been shipped to the customer
    DELIVERED = "Delivered"  # Order has been delivered to the customer
    CANCELED = "Canceled"  # Order was canceled
    RETURNED = "Returned"  # Order was returned by the customer


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer(), primary_key=True)
    size = db.Column(db.Enum(Sizes), default=Sizes.SMALL)
    color = db.Column(db.Enum(Colors), default=Colors.WHITE)
    design = db.Column(db.Enum(PrintDesigns), default=PrintDesigns.WANTED_POSTER)
    material = db.Column(db.Enum(Materials), default=Materials.COTTON)
    order_status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING)
    date_created = db.Column(db.DateTime(), default=datetime.utcnow)
    date_updated = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    quantity=db.Column(db.Integer())
    #relationship
    #user = db.Column(db.Integer(), db.ForeignKey('users.id'))
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))

    def __repr__(self):
        return f"<Order {self.id}>"
    
    def save(self):
        db.session.add(self)
        db.session.commit()


    @classmethod
    def get_by_id(cls,id):
        return cls.query.get_or_404(id)


    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Resource(db.Model):
    __tablename__ = 'resources'
    id = db.Column(db.Integer(), primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer(), nullable=False)

    def __repr__(self):
        return f"<Resource {self.name}>"

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)

    def delete(self):
        db.session.delete(self)
        db.session.commit()