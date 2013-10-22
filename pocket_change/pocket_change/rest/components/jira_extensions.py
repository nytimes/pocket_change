from pocket_change.rest.util import Preserializer, JiraRelatedResource
from pocket_change.rest.components import kaichu
from flask import g, request, current_app
from pocket_change import sqlalchemy_db
from flask.ext.restful import Resource
from flask.ext.restful.reqparse import RequestParser
from flask.ext.login import current_user
from pocket_change.auth import get_user_from_token, PocketChangeUser
from datetime import timedelta


@Preserializer.test_cycle.expand_handler('jira_issue')
@Preserializer.case_execution.expand_handler('jira_issue')
def expand_issue(issue_row, expand_tree=None):
    
    if expand_tree is None:
        expand_tree = {}
    if issue_row and issue_row.issue_id:
        issue = g.jira.issue(str(issue_row.issue_id))
        out = {'id' : issue.id, 'key' : issue.key,
               'summary' : issue.fields.summary,
               'description' : issue.fields.description,
               'status' : {'id' : issue.fields.status.id,
                           'name' : issue.fields.status.name}}
        if issue.fields.resolution:
            out['resolution'] = {'id' : issue.fields.resolution.id,
                                 'name' : issue.fields.resolution.name}
        return out
    return {}


@JiraRelatedResource.plugin('process_search_data')
def filter_by_jira_issue(resource, expand=None, query=None, **kwargs):
    
    if not query:
        query = sqlalchemy_db.session.query(resource.__class__.db_model)
    try:
        issue_id = int(request.args['issue_id'])
    except KeyError:
        issue_id = None
    else:
        query = (query.join(resource.__class__.jira_issue_db_model)
                 .filter(resource.__class__.jira_issue_db_model.issue_id==issue_id))
    try:
        issue_key = request.args['issue_key']
    except KeyError:
        pass
    else:
        try:
            issue_id_from_key = g.jira.issue(issue_key).id
        except:
            kwargs['search_result'] = []
            return {'data' : (resource, expand, query, kwargs),
                    'continue' : False}
        else:
            query = (query.join(resource.__class__.jira_issue_db_model)
                     .filter(resource.__class__.jira_issue_db_model.issue_id==issue_id_from_key))
            if issue_id and issue_id != issue_id_from_key:
                kwargs['search_result'] = []
                return {'data' : (resource, expand, query, kwargs),
                        'continue' : False}
    return {'data' : (resource, expand, query, kwargs),
            'continue' : True}


@kaichu.endpoint('jira_auth_data')
@kaichu.route('/jira_auth_data')
class JiraAuthData(Resource):
    
    def get(self):
        
        app_key = request.args.get('app_key', None)
        username = request.args.get('username', None)
        password = request.args.get('password', None)
        token = request.args.get('token', None)
        user = None
        if app_key and app_key == current_app.config['JIRA_APP_KEY']:
            if username:
                if token:
                    user = get_user_from_token(token, username)
                    used = False
                    if user:
                        used = user.token.use()
                        if used:
                            sqlalchemy_db.session.merge(user.token)
                            sqlalchemy_db.session.commit()
                    elif not password and not used:
                        return {'message' : 'Invalid token.'}, 400
                if password:
                    user = PocketChangeUser(None, username, password)
                    if user.is_authenticated():
                        User = sqlalchemy_db.models['User']
                        try:
                            db_user = (sqlalchemy_db.session.query(User)
                                       .filter(User.name==user.name).one())
                        except:
                            db_user = User(name=user.name, password=password)
                            sqlalchemy_db.session.add(db_user)
                            sqlalchemy_db.session.commit()
                        user.token = db_user.get_new_token(current_app.secret_key[:16],
                                                           expires=timedelta(hours=6),
                                                           max_uses=1)
                        user.token.use()
                        sqlalchemy_db.session.commit()
                    else:
                        return {'message' : 'Invalid username/password.'}, 400
                if not user:
                    return {'message' : 'Must provide password or token.'}, 400
            else:
                return {'message' : 'Must provide username.'}, 400
        else:
            return {'message' : 'app_key missing or invalid.'}, 400
        with open(current_app.config['JIRA_RSA_KEY_FILE'], 'r') as rsa_file:
            rsa_data = rsa_file.read()
        if hasattr(user.user, 'jira') and user.user.jira and user.user.jira.active:
            return {'rsa_key' : rsa_data,
                    'oauth_secret' : user.user.jira.oauth_secret,
                    'oauth_token' : user.user.jira.oauth_token}
        else:
            return {'message' : "User's token is expired or revoked."}, 400