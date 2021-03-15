# from marshmallow import Schema, fields, validate
from app import db
import enum
from datetime import datetime
from ourCloud.OcStaticVars import OC_CATALOGOFFERINGS, OC_CATALOGOFFERING_SIZES


class OrderType(enum.Enum):
    CREATE_ORDER = 0
    DELETE_ORDER = 100
    MODIFY_ORDER = 200


class SbuType(enum.Enum):
    BE = 'BE'
    CHB_CH = 'CH-BCH'  # Enum elements can't contain minus in the key
    CH_SOB = 'CH-SOB'
    DE = 'DE'
    LI = 'LI'
    LURED = 'LU-RED'
    LU_YELLOW = 'LU-YELLOW'
    SHARED = 'SHARED'


# This is a proposition of possible order states. TODO: Verify with team.
class OrderStateType(enum.Enum):
    NEW = 'NEW'  # Order just created
    VERIFIED = 'VERIFIED'  # Order has completed verification
    BE_PROCESSING = 'BE_PROCESSING'  # Accepted by backends, implementation in progress
    BE_DONE = 'BE_DONE'  # Backend done, tests can start
    BE_FAIL = 'BE_FAIL'  # Backends reported failure
    TESTING = 'TESTING'  # Backends reported success, testing
    TEST_FAIL = 'TEST_FAIL'  # Testing unsuccessful
    TEST_SUCCESS = 'TEST_SUCCESS'  # Testing successful
    CMDB_DONE = 'CMDB_DONE'
    DONE = 'DONE'  # Order fully completed


class BackendType(enum.Enum):
    ORCHESTRA = 'ORCHESTRA'
    OURCLOUD = 'OURCLOUD'


class Person(db.Model):
    __tablename__ = 'persons'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    sbu = db.Column(db.String(100), nullable=True)
    orders = db.relationship('Order', backref='person', lazy=True)

    def __init__(self, username: str, email: str, sbu: SbuType):
        self.username = username
        self.email = email
        self.sbu = sbu.value

    def get_id(self):
        return self.id

# class PersonSchema(Schema):
#     id = fields.Email()
#     email = fields.Email()
#     sbu = fields.Str(validate=validate.OneOf([
#         'BE',
#         'CH-BCH',
#         'CH-SOB',
#         'DE',
#         'LI',
#         'LU-RED',
#         'LU-YELLOW',
#         'SHARED'
#         ]))


class OrderItem(db.Model):
    __tablename__ = 'orderitems'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reference = db.Column(db.String(80), nullable=False)
    cataloguename = db.Column(db.String(500), nullable=False)
    size = db.Column(db.String(50), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    order = db.relationship("Order", back_populates="items")

    def __init__(self, name: OC_CATALOGOFFERINGS, size: OC_CATALOGOFFERING_SIZES):
        self.cataloguename = name.cataloguename
        self.size = size.cataloguesize

    def set_reference(self, reference):
        self.reference = reference

    def get_reference(self):
        return self.reference

    def get_cataloguename(self) -> OC_CATALOGOFFERINGS:
        return self.cataloguename

    def is_Vm(self) -> bool:
        return self.cataloguename in (OC_CATALOGOFFERINGS.WINS2019.cataloguename,
                                      OC_CATALOGOFFERINGS.RHEL7.cataloguename)

    def get_size(self) -> OC_CATALOGOFFERING_SIZES:
        return self.size


# class OrderItemSchema(Schema):
#     id = fields.Integer()
#     reference = fields.Str()
#     item_type = fields.Str()  # TODO: Add validation for the known types


class OrderStatus(db.Model):
    __tablename__ = 'orderstati'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    state = db.Column(db.Enum(OrderStateType), nullable=False)
    since = db.Column(db.DateTime, index=True, default=datetime.now)
    system = db.Column(db.Enum(BackendType))
    # This attribute might actually be a dupe of the dbrel parent_order
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))

    def __repr__(self):
        return f"<OrderStatus {self.id!r} for Order {self.order.id!r}>"

# class OrderStatusSchema(Schema):
#     id = fields.Integer()
#     state = fields.Str()  # TODO: Add ENUM here
#     since = fields.DateTime()
#     system = fields.Str()  # TODO: Add ENUM for existing backend systems, Is this actually needed.


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    create_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    requester = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False)
    type = db.Column(db.String(20))
    history = db.relationship('OrderStatus', backref='order', lazy=True)
    items = db.relationship('OrderItem', back_populates='order', lazy=True)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'order'
    }

    def __init__(self, order_type: OrderType, items, requester: Person):
        self.order_type = order_type.value
        self.items: list = items
        self.requester = requester.get_id()

    def __repr__(self):
        return f"<Order {self.id!r}>"

    def add_item(self, item):
        self.items.append(item)

    def get_items(self) -> list:
        return self.items

    def set_requester(self, requester: Person):
        self.requester = requester.get_id()

    def get_requester(self):
        return self.requester

    def get_type(self) -> OrderType:
        return OrderType(self.order_type)

    def set_type(self, order_type: OrderType):
        self.order_type = order_type.value


class CreateOrder(Order):

    __mapper_args__ = {
        'polymorphic_identity': 'createorder'
    }


class DeleteOrder(Order):

    __mapper_args__ = {
        'polymorphic_identity': 'deleteorder'
    }


class ModifyOrder(Order):

    __mapper_args__ = {
        'polymorphic_identity': 'modifyorder'
    }

# class OrderSchema(Schema):
#     id = fields.Integer()
#     create_date = fields.DateTime()
#     history = fields.Nested(OrderStatusSchema())  # All status updates
#     requestor = PersonSchema()
#     items = fields.Nested(OrderItemSchema()
