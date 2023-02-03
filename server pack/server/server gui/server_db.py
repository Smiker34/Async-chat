from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime, Text
from sqlalchemy.orm import mapper, sessionmaker
import datetime


class Storage:
    class Users:
        def __init__(self, username):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.passwd_hash = passwd_hash
            self.id = None

    class Active:
        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    class Logins:
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    class Contacts:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    class History:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        self.database_engine = create_engine(f'sqlite:///{path}.sqlite', echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})
        self.metadata = MetaData()

        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime),
                            Column('passwd_hash', String),
                            Column('pubkey', Text)
                            )

        active_table = Table('Active', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'), unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )

        logins_table = Table('Logins', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String)
                                   )

        contacts = Table('Contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user', ForeignKey('Users.id')),
                         Column('contact', ForeignKey('Users.id'))
                         )

        history_table = Table('History', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('Users.id')),
                                    Column('sent', Integer),
                                    Column('accepted', Integer)
                                    )

        self.metadata.create_all(self.database_engine)
        mapper(self.Users, users_table)
        mapper(self.Active, active_table)
        mapper(self.Logins, logins_table)
        mapper(self.Contacts, contacts)
        mapper(self.History, history_table)

        session = sessionmaker(bind=self.database_engine)
        self.session = session()
        self.session.query(self.Active).delete()
        self.session.commit()

    def add_user(self, name, passwd_hash):
        user_row = self.Users(name, passwd_hash)
        self.session.add(user_row)
        self.session.commit()
        history_row = self.History(user_row.id)
        self.session.add(history_row)
        self.session.commit()

    def remove_user(self, name):
        user = self.session.query(self.Users).filter_by(name=name).first()
        self.session.query(self.Active).filter_by(user=user.id).delete()
        self.session.query(self.Logins).filter_by(name=user.id).delete()
        self.session.query(self.Contacts).filter_by(user=user.id).delete()
        self.session.query(self.Contacts).filter_by(contact=user.id).delete()
        self.session.query(self.History).filter_by(user=user.id).delete()
        self.session.query(self.Users).filter_by(name=name).delete()
        self.session.commit()

    def get_hash(self, name):
        user = self.session.query(self.Users).filter_by(name=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        user = self.session.query(self.Users).filter_by(name=name).first()
        return user.pubkey

    def check_user(self, name):
        if self.session.query(self.Users).filter_by(name=name).count():
            return True
        else:
            return False

    def user_logout(self, username):
        user = self.session.query(self.Users).filter_by(name=username).first()
        self.session.query(self.Active).filter_by(user=user.id).delete()
        self.session.commit()

    def process_message(self, sender, recipient):
        sender = self.session.query(self.Users).filter_by(name=sender).first().id
        recipient = self.session.query(self.Users).filter_by(name=recipient).first().id
        sender_row = self.session.query(self.History).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.History).filter_by(user=recipient).first()
        recipient_row.accepted += 1
        self.session.commit()

    def add_contact(self, user, contact):
        user = self.session.query(self.Users).filter_by(name=user).first()
        contact = self.session.query(self.Users).filter_by(name=contact).first()

        if not contact or self.session.query(self.Contacts).filter_by(user=user.id, contact=contact.id).count():
            return

        contact_row = self.Contacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, user, contact):
        user = self.session.query(self.Users).filter_by(name=user).first()
        contact = self.session.query(self.Users).filter_by(name=contact).first()
        if not contact:
            return
        print(self.session.query(self.Contacts).filter(
            self.Contacts.user == user.id,
            self.Contacts.contact == contact.id
        ).delete())
        self.session.commit()

    def users_list(self):
        query = self.session.query(
            self.Users.name,
            self.Users.last_login,
        )
        return query.all()

    def active_users_list(self):
        query = self.session.query(
            self.Users.name,
            self.Active.ip_address,
            self.Active.port,
            self.Active.login_time
            ).join(self.Users)
        return query.all()

    def login_history(self, username=None):
        query = self.session.query(self.Users.name,
                                   self.Logins.date_time,
                                   self.Logins.ip,
                                   self.Logins.port
                                   ).join(self.Users)
        if username:
            query = query.filter(self.Users.name == username)
        return query.all()

    def get_contacts(self, username):
        user = self.session.query(self.Users).filter_by(name=username).one()
        query = self.session.query(self.Contacts, self.Users.name).filter_by(user=user.id)\
            .join(self.Users, self.Contacts.contact == self.Users.id)
        return [contact[1] for contact in query.all()]

    def message_history(self):
        query = self.session.query(
            self.Users.name,
            self.Users.last_login,
            self.History.sent,
            self.History.accepted
        ).join(self.Users)
        return query.all()


if __name__ == '__main__':
    test_db = Storage("test")
    test_db.user_login('test1', '192.168.1.113', 8080)
    test_db.user_login('test2', '192.168.1.113', 8081)
    print(test_db.users_list())
    print(test_db.active_users_list())
    test_db.user_logout('test2')
    print(test_db.login_history('test'))
    test_db.add_contact('test2', 'test1')
    test_db.add_contact('test1', 'test2')
    test_db.add_contact('test1', 'test3')
    test_db.remove_contact('test1', 'test3')
    test_db.process_message('test2', 'test1')
    print(test_db.message_history())
