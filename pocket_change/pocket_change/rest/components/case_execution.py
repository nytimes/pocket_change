from pocket_change.rest.util import Preserializer, JiraRelatedResource
from pocket_change.rest.components import sneeze
from pocket_change import sqlalchemy_db


case_execution_to_dict = Preserializer('case_execution',
                                       id=Preserializer.int_,
                                       description=Preserializer.str_,
                                       result=Preserializer.str_,
                                       start_time=Preserializer.datetime_(),
                                       end_time=lambda time: None if time is None else Preserializer.datetime_()(time))

@case_execution_to_dict.expand_handler('case')
def case(case_, expand_tree=None):
    
    if expand_tree is None:
        expand_tree = {}
    return Preserializer.case(case_, expand_tree=expand_tree)


@sneeze.endpoint('case_execution')
@sneeze.route('/search/case_execution')
@sneeze.route('/case_execution/<int:case_execution_id>')
class CaseExecutionResource(JiraRelatedResource):
    
    _plugins = {}
    preserializer = case_execution_to_dict
    db_model = sqlalchemy_db.models['CaseExecution']
    jira_issue_db_model = sqlalchemy_db.models.get('CaseExecutionIssue', None)
    
    def get(self, case_execution_id=None):
        
        process_search_result = self.process_search_data(id=case_execution_id)
        try:
            return process_search_result['kwargs']['search_result']
        except KeyError:
            return [case_execution_to_dict(case_execution, expand=process_search_result['expand'])
                    for case_execution in process_search_result['query'].all()]