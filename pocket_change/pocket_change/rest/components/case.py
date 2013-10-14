from pocket_change.rest.util import Preserializer, DBEntityResource
from pocket_change.rest.components import sneeze
from flask import g, request
from pocket_change import sqlalchemy_db


case_to_dict = Preserializer('case',
                             id=Preserializer.int_,
                             label=Preserializer.str_)


@sneeze.endpoint('case')
@sneeze.route('/search/case')
@sneeze.route('/case/<int:case_id>')
class CaseResource(DBEntityResource):
    
    _plugins = {}
    preserializer = case_to_dict
    db_model = sqlalchemy_db.models['Case']
    
    def get(self, case_id=None):
        
        process_search_data = self.process_search_data
        process_search_data(id=case_id)
        try:
            return process_search_data['kwargs']['search_result']
        except KeyError:
            return [case_to_dict(case, expand=process_search_data['expand'])
                    for case in process_search_data['query'].all()]


@CaseResource.plugin('process_search_data')
def filter_by_execution(resource, expand=None, query=None, **kwargs):
    
    if not query:
        query = sqlalchemy_db.session.query(resource.__class__.db_model)
    try:
        execution_id = request.args['case_execution_id']
    except KeyError:
        pass
    else:
        query = (query.join(sqlalchemy_db.models['CaseExecution'])
                 .filter(sqlalchemy_db.models['CaseExecution'].id==execution_id))
    return {'data' : (resource, expand, query, kwargs),
            'continue' : True}