from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

child_parent = db.Table(
    'child_parent',
    db.Column('child_id', db.Integer, db.ForeignKey('childhood.children.id'), primary_key=True),
    db.Column('parent_id', db.Integer, db.ForeignKey('childhood.parents.id'), primary_key=True),
    schema='childhood'
)

class Group(db.Model):
    __tablename__ = 'groups'
    __table_args__ = {'schema': 'childhood'}

    id = db.Column(db.Integer, primary_key=True)
    group_number = db.Column(db.String(20), nullable=False)

    children = db.relationship('Child', back_populates='group')
    educators = db.relationship('Educator', back_populates='group')

class Child(db.Model):
    __tablename__ = 'children'
    __table_args__ = {'schema': 'childhood'}

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey('childhood.groups.id')
    )

    group = db.relationship('Group', back_populates='children')
    parents = db.relationship('Parent', secondary=child_parent, back_populates='children')
    attendances = db.relationship('Attendance', back_populates='child')
    payments = db.relationship('Payment', back_populates='child')

class Parent(db.Model):
    __tablename__ = 'parents'
    __table_args__ = {'schema': 'childhood'}

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))

    children = db.relationship('Child', secondary=child_parent, back_populates='parents')

class Educator(db.Model):
    __tablename__ = 'educators'
    __table_args__ = {'schema': 'childhood'}

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    experience = db.Column(db.Integer)
    hire_date = db.Column(db.Date)
    groups = db.relationship('Group', secondary='childhood.group_educator', back_populates='educators')

group_educator = db.Table(
    'group_educator',
    db.Column('group_id', db.Integer, db.ForeignKey('childhood.groups.id'), primary_key=True),
    db.Column('educator_id', db.Integer, db.ForeignKey('childhood.educators.id'), primary_key=True),
    schema='childhood'
)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    __table_args__ = {'schema': 'childhood'}

    id = db.Column(db.Integer, primary_key=True)
    absence_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    child_id = db.Column(
        db.Integer,
        db.ForeignKey('childhood.children.id'),
        nullable=False
    )

    child = db.relationship('Child', back_populates='attendances')

class Payment(db.Model):
    __tablename__ = 'payments'
    __table_args__ = {'schema': 'childhood'}

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    period = db.Column(db.String(7), nullable=False)
    child_id = db.Column(
        db.Integer,
        db.ForeignKey('childhood.children.id'),
        nullable=False
    )

    child = db.relationship('Child', back_populates='payments')

Group.children = db.relationship('Child', back_populates='group')
Group.educators = db.relationship('Educator', secondary=group_educator, back_populates='groups')