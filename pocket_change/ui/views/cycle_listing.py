from pocket_change.ui import core
from pocket_change import sqlalchemy_db
from flask import current_app, request, render_template, url_for, g
from flask.ext.login import current_user
from sqlalchemy import or_


@core.route('/test_cycle_list/', methods=['POST', 'GET'])
@core.route('/test_cycle_list/<int:offset>', methods=['POST', 'GET'])
@core.route('/test_cycle_list/<filter>', methods=['POST', 'GET'])
@core.route('/test_cycle_list/<filter>/<int:offset>', methods=['POST', 'GET'])
def cycle_listing(filter=None, offset=1):
    
    TestCycle = sqlalchemy_db.models['TestCycle']
    query = sqlalchemy_db.session.query(TestCycle)
    if request.method == 'POST':
        filter = request.form.get('filter', None)
        offset = 1
    if filter:
        query = query.filter(or_(TestCycle.name.contains(filter),
                                 TestCycle.description.contains(filter)))
    query = query.order_by(TestCycle.id.desc())
    if offset == 1:
        query = query.limit(21)
        cycles = query.all()
        cycle_list = cycles[:20]
        has_next = (len(cycles) == 21)
    else:
        query = query.limit(22).offset(((offset - 1) * 20) - 1)
        cycles = query.all()
        cycle_list = cycles[1:22]
        has_next = (len(cycles) == 22)
    cycle_issues = {}
    use_jira = bool(current_app.config['KAICHU_ENABLED']
                    and current_user and current_user.is_authenticated()
                    and hasattr(current_user, 'user') and current_user.user
                    and hasattr(current_user.user, 'jira') and current_user.user.jira
                    and current_user.user.jira.active)
    if use_jira:
        for cycle in cycle_list:
            if cycle.jira_issue and cycle.jira_issue.issue_id:
                cycle_issues[cycle.id] = g.jira.issue(str(cycle.jira_issue.issue_id))
    return render_template('cycle_listing.html',
                           filter=filter,
                           offset=offset,
                           cycle_list=cycle_list,
                           has_next=has_next,
                           use_jira=use_jira,
                           jira_host=current_app.config.get('JIRA_HOST', ''),
                           cycle_issues=cycle_issues)