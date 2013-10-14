from flask.ext.restful import Resource
from pocket_change.rest.components import sneeze
from pocket_change import sqlalchemy_db
from flask import request, current_app
from pocket_change.auth import PocketChangeUser, get_user_from_token
from datetime import timedelta


@sneeze.endpoint('token')
@sneeze.route('/token')
class Token(Resource):
    
    def get(self):
        
        username = request.args.get('username', None)
        password = request.args.get('password', None)
        token = request.args.get('token', None)
        app_key = request.args.get('app_key', None)
        if not (username and (password or token) and app_key):
            return {'message' : 'Missing username, password, token, and/or app_key.'}, 400
        if app_key != current_app.config['JIRA_APP_KEY']:
            return {'message' : 'Incorrect app_key.'}, 400
        user = None
        if token:
            user = get_user_from_token(token, username)
            if user and user.token.active:
                return {'token' : token}
            elif not password:
                return {'message' : 'Invalid token.'}, 400
        if password:
            user = PocketChangeUser(None, username, password)
            if user.is_authenticated():
                User = sqlalchemy_db.models['User']
                try:
                    db_user = (sqlalchemy_db.session.query(User)
                               .filter(User.name==user.name).one())
                except:
                    db_user = User(name=user.name)
                    sqlalchemy_db.session.add(db_user)
                    sqlalchemy_db.session.commit()
                    user.token = db_user.get_new_token(current_app.secret_key[:16],
                                                       expires=timedelta(hours=6),
                                                       max_uses=1)
            sqlalchemy_db.session.commit()
            return {'token' : user.token.value}
        else:
            return {'message' : 'Bad username and/or password.'}, 400
        