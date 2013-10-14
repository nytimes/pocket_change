from flask.ext.sqlalchemy import SQLAlchemy


class SQLAlchemyWrapper(SQLAlchemy):
    
    def __init__(self, app):
        
        super(SQLAlchemyWrapper, self).__init__(app)
        self.models = {}
    
    @classmethod
    def make(cls, app, *model_adders):
        
        inst = cls(app)
        for add_models in model_adders:
            inst.models.update(add_models(inst.Model))
        return inst


class SQLAlchemyWrapperProxy(object):
    
    def __init__(self):
        
        object.__setattr__(self, 'inst', None)
    
    def make(self, app, *model_adders):
        
        inst = SQLAlchemyWrapper.make(app, *model_adders)
        inst.create_all()
        self.inst = inst
    
    def __getattribute__(self, name):
        
        inst = object.__getattribute__(self, 'inst') 
        if inst:
            return getattr(inst, name)
        else:
            return object.__getattribute__(self, name)
    
    def __setattr__(self, name, value):
        
        inst = object.__getattribute__(self, 'inst') 
        if inst:
            setattr(inst, name, value)
        else:
            object.__setattr__(self, name, value)