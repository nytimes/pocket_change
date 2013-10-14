from pocket_change.ui import kaichu
from flask import request, current_app, redirect, url_for, render_template, g
from flask.ext.login import current_user
from datetime import datetime, timedelta
from requests_oauthlib.oauth1_session import OAuth1Session
from requests_oauthlib import OAuth1
from oauthlib.oauth1 import SIGNATURE_RSA
from pocket_change import sqlalchemy_db
from requests import Session


@kaichu.route('/link_jira/', methods=['GET', 'POST'])
def start_linking():
    
    if (hasattr(current_user.user, 'jira') and current_user.user.jira
        and current_user.user.jira.active and current_user.user.jira.expires is not None):
        # TODO: Correct manually revoked jira oauth token
        return 'link already active'
    if request.method == 'POST':
        with open(current_app.config['JIRA_RSA_KEY_FILE'], 'r') as rsa_file:
            rsa_data = rsa_file.read()
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        jira_host = current_app.config['JIRA_HOST'].rstrip('/')
        if g.jira.verify_credentials(username, password):
            oauth_session = OAuth1Session(current_app.config['JIRA_APP_KEY'],
                                          signature_method=SIGNATURE_RSA,
                                          rsa_key=rsa_data)
            token_response = oauth_session.fetch_request_token(jira_host + '/plugins/servlet/oauth/request-token')
            db_user = sqlalchemy_db.session.merge(current_user.user)
            if hasattr(db_user, 'jira') and db_user.jira and db_user.jira is not None:
                db_user.jira.name = username
                db_user.jira.oauth_token = token_response['oauth_token']
                db_user.jira.oauth_secret = token_response['oauth_token_secret']
                db_user.jira.expires=None
                db_user.jira.revoked=False
            else:
                db_user.jira = sqlalchemy_db.models['UserJiraData'](name=username,
                                                                    oauth_token=token_response['oauth_token'],
                                                                    oauth_secret=token_response['oauth_token_secret'],
                                                                    expires=None,
                                                                    revoked=False)
            sqlalchemy_db.session.commit()
            auth_url = oauth_session.authorization_url(jira_host + '/plugins/servlet/oauth/authorize')
            return redirect(auth_url + '&redirect_uri=' + current_app.config['APP_HOST'] + ':' + current_app.config['APP_PORT'] + url_for('kaichu_ui.complete_link'))
        else:
            return 'Bad username/password'
    else:
        return render_template('jira_linking.html', user=current_user)

@kaichu.route('/jira_oauth_callback/')
@kaichu.route('/complete_link/')
def complete_link():
    
        token = request.args.get('oauth_token', None)
        if not token or current_user.user.jira.oauth_token != token:
            return 'Linking failed'
        with open(current_app.config['JIRA_RSA_KEY_FILE'], 'r') as rsa_file:
            rsa_data = rsa_file.read()
        oauth_session = OAuth1Session(current_app.config['JIRA_APP_KEY'],
                                      signature_method=SIGNATURE_RSA,
                                      rsa_key=rsa_data,
                                      resource_owner_key=current_user.user.jira.oauth_token,
                                      resource_owner_secret=current_user.user.jira.oauth_secret)
        jira_host = current_app.config['JIRA_HOST'].rstrip('/')
        token_response = oauth_session.fetch_access_token(jira_host + '/plugins/servlet/oauth/access-token')
        db_user = sqlalchemy_db.session.merge(current_user.user)
        db_user.jira.oauth_token = token_response['oauth_token']
        db_user.jira.oauth_secret = token_response['oauth_token_secret']
        db_user.jira.expires = datetime.now() + timedelta(seconds=int(token_response['oauth_expires_in']))
        sqlalchemy_db.session.commit()
        g.jira._session.auth = OAuth1(current_app.config['JIRA_APP_KEY'],
                                      signature_method=SIGNATURE_RSA,
                                      rsa_key=rsa_data,
                                      resource_owner_key=db_user.jira.oauth_token,
                                      resource_owner_secret=db_user.jira.oauth_secret)
        g.jira.priorities()
        return redirect(url_for('core_ui.cycle_listing'))