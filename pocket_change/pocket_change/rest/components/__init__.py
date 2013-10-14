from pocket_change.rest.util import RestfulApi
from pocket_change.rest import api
from flask.ext.restful import Resource
from flask import current_app


sneeze = RestfulApi(api)
pocket = RestfulApi(api)
kaichu = RestfulApi(api)


@sneeze.endpoint('ping')
@sneeze.route('/')
class PingResource(Resource):
    
    def get(self):
        
        result = {'features' : ['core']}
        if current_app.config['KAICHU_ENABLED']:
            result['features'].append('kaichu')
        return result

def load(app):
    
    import pocket_change.rest.components.case
    import pocket_change.rest.components.case_execution
    import pocket_change.rest.components.test_cycle
    import pocket_change.rest.components.auth
    if app.config['KAICHU_ENABLED']:
        import pocket_change.rest.components.jira_extensions