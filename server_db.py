from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime


class Storage:
    class Users:
        def __init__(self, username):
            self.name = username
            self.last_login = datetime.datetime.now()
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

    def __init__(self):
        self.database_engine = create_engine('sqlite:///server_db.sqlite', echo=False, pool_recycle=7200)
        self.metadata = MetaData()

        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime)
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

        self.metadata.create_all(self.database_engine)
        mapper(self.Users, users_table)
        mapper(self.Active, active_table)
        mapper(self.Logins, logins_table)

        session = sessionmaker(bind=self.database_engine)
        self.session = session()
        self.session.query(self.Active).delete()
        self.session.commit()

    def user_login(self, username, ip_address, port):
        print(username, ip_address, port)
        res = self.session.query(self.Users).filter_by(name=username)

        if res.count():
            user = res.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.Users(username)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.Active(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.Logins(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        user = self.session.query(self.Users).filter_by(name=username).first()
        self.session.query(self.Active).filter_by(user=user.id).delete()
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


if __name__ == '__main__':
    test_db = Storage()
    test_db.user_login('client_1', '192.168.1.4', 8888)
    test_db.user_login('client_2', '192.168.1.5', 7777)
    print(test_db.active_users_list())
    test_db.user_logout('client_1')
    print(test_db.active_users_list())
    test_db.login_history('client_1')
    print(test_db.users_list())
