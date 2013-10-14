from pocket_change.rest.util import Preserializer, JiraRelatedResource
from pocket_change.rest.components import sneeze
from flask import g
from pocket_change import sqlalchemy_db


cycle_to_dict = Preserializer('test_cycle',
                              id=Preserializer.int_,
                              name=Preserializer.str_,
                              description=Preserializer.str_,
                              running_count=Preserializer.int_)

@cycle_to_dict.expand_handler('case_executions')
def case_executions(executions, expand_tree=None):
    
    if expand_tree is None:
        expand_tree = {}
    return [Preserializer.case_execution(execution, expand_tree=expand_tree) for execution in executions]


@sneeze.endpoint('test_cycle')
@sneeze.route('/search/test_cycle')
@sneeze.route('/test_cycle/<int:test_cycle_id>')
class TestCycleResource(JiraRelatedResource):
    
    _plugins = {}
    preserializer = cycle_to_dict
    db_model = sqlalchemy_db.models['TestCycle']
    jira_issue_db_model = sqlalchemy_db.models.get('TestCycleIssue', None)
    
    def get(self, test_cycle_id=None):
        
        process_search_data = self.process_search_data
        process_search_data(id=test_cycle_id)
        try:
            return process_search_data['kwargs']['search_result']
        except KeyError:
            return [cycle_to_dict(cycle, expand=process_search_data['expand'])
                    for cycle in process_search_data['query'].all()]