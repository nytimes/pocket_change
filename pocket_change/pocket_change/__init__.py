#### DB SETUP ####

from pocket_change.database import SQLAlchemyWrapperProxy
sqlalchemy_db = SQLAlchemyWrapperProxy()
from sneeze.database.models import add_models as sneeze_models
from pocket.database import add_models as pocket_models

model_adders = [sneeze_models, pocket_models]


#### APP CONFIG ####

from flask import Flask, render_template, request, session


class AppContextClass(Flask.app_ctx_globals_class):
    
    @property
    def jira(self):
        
        try:
            return self._jira
        except AttributeError:
            self._jira = JiraClient({'server' : app.config['JIRA_HOST']})
            return self._jira



Flask.app_ctx_globals_class = AppContextClass
app = Flask(__name__.split()[0])
app.config.from_envvar('POCKET_CHANGE_CONFIG')

##### KAICHU ####

from pocket_change.jira_lib import Client as JiraClient
try:
    from kaichu.models import add_models as kaichu_models
except ImportError:
    kaichu_models = None

if (JiraClient and kaichu_models
    and app.config.get('JIRA_HOST', False)
    and app.config.get('JIRA_APP_KEY', False)
    and app.config.get('JIRA_RSA_KEY_FILE', False)):
    app.config['KAICHU_ENABLED'] = True
    model_adders.append(kaichu_models)
else:
    app.config['KAICHU_ENABLED'] = False

#### DB INIT ####

sqlalchemy_db.make(app, *model_adders)

#### AUTH ####

from pocket_change.auth import login_manager
login_manager.init_app(app)

#### REST ####

from pocket_change.rest import api
from pocket_change.rest.components import load as load_rest_components
load_rest_components(app)
app.register_blueprint(api, url_prefix='/rest')

#### GUI ####

from pocket_change.ui import load as load_ui, core as core_ui
load_ui(app)
app.register_blueprint(core_ui)
if app.config['KAICHU_ENABLED']:
    from pocket_change.ui import kaichu as kaichu_ui
    app.register_blueprint(kaichu_ui)


if __name__ == '__main__':
    
    app.run(host='0.0.0.0')