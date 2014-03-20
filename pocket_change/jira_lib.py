try:
    from jira.client import JIRA
except ImportError, e:
    JIRA = None
    Client = None
    get_rsa_key = None
else:
    from flask.ext.login import current_user
    from flask import current_app
    import requests
    from requests_oauthlib import OAuth1
    from oauthlib.oauth1 import SIGNATURE_RSA
    
    
    class Client(JIRA):
        
        def __init__(self, options=None):
            
            if options is None:
                options = {}
        
            self._options = JIRA.DEFAULT_OPTIONS
            self._options.update(options)
        
            # rip off trailing slash since all urls depend on that
            self._options['server'] = self._options['server'].rstrip('/')
        
            self._try_magic()
            
            self._session = requests.Session()
            self._session.verify = self._options['verify']
            if (hasattr(current_user, 'user') and current_user.user
                and hasattr(current_user.user, 'jira') and current_user.user.jira
                and current_user.user.jira.active
                and hasattr(current_user.user.jira, 'expires') and current_user.user.jira.expires is not None
                and 'JIRA_RSA_KEY_FILE' in current_app.config):
                self.add_oauth()
        
        def add_oauth(self):
            
            with open(current_app.config['JIRA_RSA_KEY_FILE'], 'r') as rsa_file:
                rsa_data = rsa_file.read()
            self._session.auth = OAuth1(current_app.config['JIRA_APP_KEY'],
                                        rsa_key=rsa_data,
                                        signature_method=SIGNATURE_RSA,
                                        resource_owner_key=current_user.user.jira.oauth_token,
                                        resource_owner_secret=current_user.user.jira.oauth_secret)
        
        def verify_credentials(self, username, password):
            
            auth_result = self._session.post('%s/rest/auth/1/session'
                                             % self._options['server'],
                                             data=('{"username" : "%s", "password" : "%s"}'
                                                   % (username, password)),
                                             headers={'content-type' : 'application/json'})
            if auth_result.status_code == 200:
                logout_result = self._session.delete('%s/rest/auth/1/session'
                                     % self._options['server'])
                return True
            else:
                return False