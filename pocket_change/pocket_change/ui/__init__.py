from flask import Blueprint
import os


core = Blueprint('core_ui', __name__,
                 static_folder='static',
                 template_folder='templates')
kaichu = Blueprint('kaichu_ui', __name__,
                   static_folder='static',
                   template_folder='templates')

def load(app):
    
    import pocket_change.ui.views.cycle_listing
    import pocket_change.ui.views.cycle_case_rollup
    import pocket_change.ui.views.case_execution_details
    import pocket_change.ui.views.login
    if app.config['KAICHU_ENABLED']:
        import pocket_change.ui.jira_extensions
        import pocket_change.ui.views.jira_linking