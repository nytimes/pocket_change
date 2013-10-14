from flask import request, url_for, session, g
from flask.ext.restful import Api, Resource
from collections import defaultdict
from functools import partial
from pocket_change import sqlalchemy_db
from itertools import chain


class RestfulApi(Api):
    
    def __init__(self, *args, **kwargs):
        
        super(RestfulApi, self).__init__(*args, **kwargs)
        self.route_map = defaultdict(set)
    
    def route(self, path):
        
        def _route(resource):
            
            self.route_map[resource].add(path)
            return resource
        
        return _route
    
    def endpoint(self, name=None):
        
        def _endpoint(resource):
            
            if name:
                self.add_resource(resource, *self.route_map[resource], endpoint=name)
            else:
                self.add_resource(resource, *self.route_map[resource])
            return resource
        
        return _endpoint
    
    def init_app(self, app):
        """Initialize this class with the given :class:`flask.Flask`
        application or :class:`flask.Blueprint` object.

        :param app: the Flask application or blueprint object
        :type app: flask.Flask
        :type app: flask.Blueprint

        Examples::

            api = Api()
            api.init_app(app)
            api.add_resource(...)

        """
        self.app = app
        self.endpoints = set()
        # If app is a blueprint, defer the initialization 
        try:
            app.record(self._deferred_blueprint_init)
        except AttributeError:
            self._init_app(app)
        else:
            if app.url_prefix and not self.prefix:
                self.prefix = app.url_prefix
            elif self.prefix and not app.url_prefix:
                app.url_prefix = self.prefix
            elif app.url_prefix and self.prefix and app.url_prefix != self.prefix:
                raise ValueError("Cannot resolve url prefix; restful api and "
                                 "blueprint both have prefixes but they do not match.")
    
    def _deferred_blueprint_init(self, setup_state):
        """Synchronize prefix between blueprint/api and registration options, then
        perform initialization with setup_state.app :class:`flask.Flask` object.  
        When a :class:`flask_restful.Api` object is initialized with a blueprint, 
        this method is recorded on the blueprint to be run when the blueprint is later
        registered to a :class:`flask.Flask` object.
        :param setup_state: The setup state object passed to deferred functions 
        during blueprint registration
        :type setup_state: flask.blueprints.BlueprintSetupState
        
        """
        if not setup_state.first_registration:
            raise ValueError('flask-restful blueprints can only be registered once.')
        if setup_state.url_prefix:
            self.prefix = setup_state.url_prefix
        elif self.prefix:
            setup_state.url_prefix = setup_state.options['url_prefix'] = self.prefix
        self._init_app(setup_state.app)
    
    def _init_app(self, app):
        """Perform initialization actions with the given :class:`flask.Flask`
        object.
        :param app: The flask application object
        :type app: flask.Flask
        
        """
        self.app = app
        app.handle_exception = partial(self.error_router, app.handle_exception)
        app.handle_user_exception = partial(self.error_router, app.handle_user_exception)


class Preserializer(object):
    
    def __init__(self, _name, **default_attribute_field_map):
        
        for attribute_name, mapped_data in default_attribute_field_map.iteritems():
            if callable(mapped_data):
                default_attribute_field_map[attribute_name] = (attribute_name, mapped_data)
        self.map = default_attribute_field_map
        self.expand_map = {}
        setattr(Preserializer, _name, self)
    
    def __call__(self, inst, **kwargs):
        
        out = {}
        for attribute_name, parse_data in self.map.iteritems():
            field_name, handler = parse_data
            out[field_name] = handler(getattr(inst, attribute_name))
        try:
            expand_tree = kwargs['expand_tree']
        except KeyError:
            expand_tree = {}
            for entity in kwargs.get('expand', []):
                cursor = expand_tree
                for part in entity.split('.'):
                    if part not in cursor:
                        cursor[part] = {}
                    cursor = cursor[part]
        for attribute_name, sub_tree in expand_tree.iteritems():
            try:
                field_name, handler = self.expand_map[attribute_name]
            except KeyError:
                pass
            else:
                try:
                    data = getattr(inst, attribute_name)
                except AttributeError:
                    pass
                else:
                    out[field_name] = handler(data, sub_tree)
        return out
    
    @staticmethod
    def str_(data, expand_tree={}):
        
        return str(data)
    
    @staticmethod
    def int_(data, expand_tree={}):
        
        return int(data)
    
    @staticmethod
    def float_(data, expand_tree={}):
        
        return float(data)
    
    @staticmethod
    def datetime_(format_string='%Y-%m-%d %H:%M:%S'):
        
        def _datetime_(data, expand_tree={}):
            
            return data.strftime(format_string)
        
        return _datetime_
    
    def expand_handler(self, attribute_name, field_name=None):
        
        if not field_name:
            field_name = attribute_name
        
        def add_expand_handler(func):
            
            self.expand_map[attribute_name] = (field_name, func)
            return func
        
        return add_expand_handler


class PluginGroup(object):
    
    def __init__(self, resource, plug=None, *arg_names):
        
        self.resource = resource
        if plug:
            self.plugs = [plug]
        else:
            self.plugs = []
        self.arg_names = arg_names
        self.return_value = None
    
    def __call__(self, *args, **kwargs):
        
        if not self.resource:
            raise TypeError('Plugins can only be called on resource instances.')
        plugin = self.plugs[-1]
        prev = plugin(self.resource, *args, **kwargs)
        for plugin in self.plugs[-2::-1]:
            if prev['continue']:
                prev = plugin(*prev['data'][:-1], **prev['data'][-1])
        self.return_value = prev['data']
        return self.return_value
    
    def __getitem__(self, key):
        
        if self.return_value is None:
            raise Exception('Plugin has not yet been run.')
        if not self.arg_names:
            raise ValueError('No arg_names specified for this plugin.')
        return self.return_value[self.arg_names.index(key)]


class PlugableResource(Resource):
    
    _plugins = {}
    _plugin_specs = {}
    preserializer = None
    
    @classmethod
    def plugin(cls, hook_name, *arg_names):
        
        def add_plugin(func):
        
            if not callable(func):
                raise TypeError('Plugins must be callable.')
            if hook_name not in cls._plugins:
                cls._plugins[hook_name] = PluginGroup(None, func, *arg_names)
            else:
                cls._plugins[hook_name].plugs.append(func)
                if arg_names:
                    cls._plugins[hook_name].arg_names = arg_names
            return func
        
        return add_plugin
    
    def __getattr__(self, name):
        
        plugin_group = PluginGroup(self)
        for base in type.mro(self.__class__):
            try:
                plugs = base._plugins
            except AttributeError:
                pass
            else:
                try:
                    base_plug_group = plugs[name]
                except KeyError:
                    pass
                else:
                    plugin_group.plugs.extend(base_plug_group.plugs)
                    if not plugin_group.arg_names and base_plug_group.arg_names:
                        plugin_group.arg_names = base_plug_group.arg_names
        if not plugin_group.plugs:
            raise AttributeError('{} has no attribute or plugin {}.'
                                 .format(self.__class__.__name__, name))
        return plugin_group


@PlugableResource.plugin('process_search_data',
                         'resource', 'expand', 'query', 'kwargs')
def build_expand(resource, expand=None, query=None, **kwargs):
    
    return {'data' : (resource, request.args.get('expand', '').split(';'), query, kwargs),
            'continue' : True}


class DBEntityResource(PlugableResource):
    
    _plugins = {}
    db_model = None


@DBEntityResource.plugin('process_search_data')
def filter_by_id(resource, expand=None, query=None, **kwargs):
    
    print kwargs
    if not query:
        query = sqlalchemy_db.session.query(resource.__class__.db_model)
    try:
        resource_id = kwargs['id']
    except KeyError:
        pass
    else:
        if resource_id is not None:
            query = query.filter(resource.__class__.db_model.id==resource_id)
            try:
                kwargs['search_result'] = resource.__class__.preserializer(query.one(), expand=expand)
            except Exception:
                kwargs['search_result'] = {}
            return {'data' : (resource, expand, query, kwargs),
                    'continue' : False}
    return {'data' : (resource, expand, query, kwargs),
            'continue' : True}


class JiraRelatedResource(DBEntityResource):
    
    _plugins = {}
    jira_issue_db_model = None