from pocket_change.ui import core
from pocket_change import sqlalchemy_db
from flask import current_app, request, render_template, session
from pocket_change.auth import PocketChangeUser
from flask.ext.login import login_user
from datetime import timedelta, datetime


login_lifetime = timedelta(days=30)


@core.route('/login/', methods=['POST', 'GET'])
def login():
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user = PocketChangeUser(None, username, password)
        User = sqlalchemy_db.models['User']
        db_session = sqlalchemy_db.create_scoped_session()
        try:
            db_user = (db_session.query(User)
                       .filter(User.name==user.name).one())
        except:
            db_user = None
            user = PocketChangeUser(None, username, password)
        else:
            user = PocketChangeUser(db_user, password=password)
        if user.is_authenticated():
            User = sqlalchemy_db.models['User']
            if db_user:
                user.populate_name_from_database()
            else:
                db_user = User(name=user.name)
                db_user.password = password
                db_session.add(db_user)
                db_session.commit()
            user.token = db_user.get_new_token(current_app.secret_key[:16],
                                               expires=datetime.now() + login_lifetime)
            db_session.commit()
            session['username'] = user.name
            login_user(user)
            return 'logged in'
        else:
            return 'login failed'
    else:
        return render_template('login.html')