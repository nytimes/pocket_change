from pocket_change.ui import core
from pocket_change import sqlalchemy_db
from flask import render_template


@core.route('/case_execution_details/<int:case_execution_id>')
def case_execution_details(case_execution_id):
    
    CaseExecution = sqlalchemy_db.models['CaseExecution']
    execution = (sqlalchemy_db.session.query(CaseExecution)
                 .filter(CaseExecution.id==case_execution_id)
                 .one())
    return render_template('case_execution_details.html',
                           case_execution=execution)