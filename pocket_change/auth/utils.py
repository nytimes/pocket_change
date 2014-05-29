from pocket_change import sqlalchemy_db
from pocket_change.auth import PocketChangeUser


User = sqlalchemy_db.models['User']
UserToken = sqlalchemy_db.models['UserToken']


class AuthedUserCreator(object):

    def postprocess_user(self, user):

        return user

    def authed_user(self):

        try:
            password = self.password
        except AttributeError:
            password = None
        else:
            try:
                password = password.data
            except AttributeError:
                pass
        try:
            token = self.token
        except AttributeError:
            token = None
        else:
            try:
                token = token.data
            except AttributeError:
                pass
        name = self.name
        try:
            name = name.data
        except AttributeError:
            pass
        if not (name and (password or token)):
            return None
        db_session = sqlalchemy_db.create_scoped_session()
        if token:
            try:
                db_token = (db_session.query(UserToken)
                            .filter(UserToken.value==token).one())
            except:
                pass
            else:
                user = PocketChangeUser(db_token, self.ttl, name)
                if user.is_authenticated():
                    return self.postprocess_user(user)
        if password:
            try:
                db_user = (db_session.query(User)
                           .filter(User.name==name).one())
            except:
                pass
            else:
                user = PocketChangeUser(db_user, self.ttl, name, password)
                if user.is_authenticated():
                    return self.postprocess_user(user)
                else:
                    # Token will have been created, so we revoke it
                    # here since auth failed, causing the token to act
                    # as a loggin attmept record as well
                    user.token = db_session.merge(user.token)
                    user.token.revoke()
                    db_session.commit()
        return None