from flask.ext.login import LoginManager
from pocket_change import sqlalchemy_db
from datetime import datetime, timedelta
from flask import current_app, session


user_data_timeout = timedelta(minutes=5)
login_timeout = timedelta(days=30)

class PocketChangeUser(object):
    
    authenticators = []
    
    def __init__(self, db_entity, name=None, password=None, populate_name_from_database=False):
        
        if db_entity:
            self.session = sqlalchemy_db.create_scoped_session()
            db_entity = self.session.merge(db_entity)
        try:
            self.token = db_entity.get_new_token(current_app.secret_key[:16],
                                                 expires=login_timeout)
        except AttributeError:
            self.token = db_entity
        else:
            self.session.commit()
        self.last_refresh = datetime.now()
        if name is None and populate_name_from_database:
            self.populate_name_from_database()
        else:
            self.name = name
        self.password = password
    
    def refresh(self, force=False):
        
        if force or datetime.now() > self.last_refresh + user_data_timeout:
            self.session = sqlalchemy_db.create_scoped_session()
            self.token = self.session.merge(self.token)
            self.last_refresh = datetime.now()
    
    @classmethod
    def authenticator(cls, func):
        
        if 'authenticators' not in cls.__dict__:
            cls.authenticators = cls.authenticators[:]
        cls.authenticators.append(func)
        return func
    
    def is_authenticated(self):
        
        try:
            self.refresh()
        except:
            pass
        for authenticator in self.__class__.authenticators:
            try:
                if authenticator(self):
                    return True
            except:
                pass
        return False
    
    def is_active(self):
        
        self.refresh()
        return self.token.active
    
    def is_anonymous(self):
        
        return False
    
    def get_id(self):
        
        return self.token.value
    
    def get_auth_token(self):
        
        return self.get_id()
    
    @property
    def user(self):
        
        if self.token and hasattr(self.token, 'user'):
            return self.token.user
        else:
            return None
    
    def populate_name_from_database(self):
        
        self.name = self.user.name

@PocketChangeUser.authenticator
def token_auth(user):
    
    return (bool(user.name and user.token)
            and user.token.verify(current_app.secret_key[:16], user.name))

@PocketChangeUser.authenticator
def password_auth(user):
    
    return (bool(user.user.name and user.password)
            and user.user.verify_password(user.password))

login_manager = LoginManager()

@login_manager.user_loader
def get_user_from_token(token, username=None):
    
    UserToken = sqlalchemy_db.models['UserToken']
    try:
        token = (sqlalchemy_db.session.query(UserToken)
                 .filter(UserToken.value==token).one())
    except:
        return None
    if username is None:
        username = session.get('username', '')
    return PocketChangeUser(token, username)

@login_manager.token_loader
def load_user_from_token(token):
    
    user = get_user_from_token(token)
    user.populate_name_from_database()
    session['username'] = user.name
    return user