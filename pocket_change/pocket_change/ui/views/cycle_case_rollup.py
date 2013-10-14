from pocket_change.ui import core
from pocket_change import sqlalchemy_db
from flask import current_app, render_template, g
from flask.ext.login import current_user
from collections import defaultdict


@core.route('/test_cycle_case_view/<int:test_cycle_id>')
def cycle_cases(test_cycle_id):
    
    CaseExecution = sqlalchemy_db.models['CaseExecution']
    TestCycle = sqlalchemy_db.models['TestCycle']
    test_cycle = sqlalchemy_db.session.query(TestCycle).filter(TestCycle.id==test_cycle_id).one()
    executions_by_case = defaultdict(list)
    cases = []
    case_ids = set()
    case_issues = defaultdict(lambda: {'issue_ids' : set(),
                                       'issues' : list()})
    cycle_issue = None
    use_jira = bool(current_app.config['KAICHU_ENABLED']
                    and current_user and current_user.is_authenticated()
                    and hasattr(current_user, 'user') and current_user.user
                    and hasattr(current_user.user, 'jira') and current_user.user.jira
                    and current_user.user.jira.active)
    for case_execution in (sqlalchemy_db.session.query(CaseExecution)
                           .filter(CaseExecution.test_cycles.contains(test_cycle))
                           .order_by(CaseExecution.id)):
        if 'Out of case scope :' not in case_execution.case.label:
            if case_execution.case_id not in case_ids:
                case_ids.add(case_execution.case_id)
                cases.append(case_execution.case)
            executions_by_case[case_execution.case_id].append(case_execution)
            if use_jira:
                try:
                    issue_id = case_execution.jira_issue.issue_id
                except:
                    pass
                else:
                    if issue_id:
                        case_issues[case_execution.case_id]['issue_ids'].add(issue_id)
    if use_jira:
        if test_cycle.jira_issue and test_cycle.jira_issue.issue_id:
            cycle_issue = g.jira.issue(str(test_cycle.jira_issue.issue_id))
        for case_id in case_ids:
            statuses = set()
            resolutions = set()
            if case_issues[case_id]['issue_ids']:
                for issue_id in case_issues[case_id]['issue_ids']:
                    issue = g.jira.issue(str(issue_id))
                    statuses.add(issue.fields.status.name)
                    if issue.fields.status.name == 'Closed':
                        resolutions.add(issue.fields.resolution.name)
                    case_issues[case_id]['issues'].append(issue)
                if len(statuses) > 1 or next(iter(statuses)) != 'Closed':
                    case_issues[case_id]['rollup_result'] = 'FAIL - UNDER REVIEW'
                else:
                    if len(resolutions) > 1:
                        case_issues[case_id]['rollup_result'] = 'FAIL - REVIEWED'
                    else:
                        resolution = next(iter(resolutions))
                        if resolution == 'Cannot Reproduce':
                            case_issues[case_id]['rollup_result'] = 'PASS - %s' % resolution.upper()
                        else:
                            case_issues[case_id]['rollup_result'] = 'FAIL - %s' % resolution.upper()
            else:
                execution_statuses = set(execution.result for execution in executions_by_case[case_id])
                if 'PENDING' in execution_statuses:
                    case_issues[case_id]['rollup_result'] = 'PENDING'
                else:
                    case_issues[case_id]['rollup_result'] = 'PASS'
            
    return render_template('cycle_case_rollup.html',
                           cycle=test_cycle,
                           cycle_issue=cycle_issue,
                           cases=cases,
                           executions_by_case=executions_by_case,
                           use_jira=use_jira,
                           jira_host=current_app.config.get('JIRA_HOST', ''),
                           case_issues=case_issues)