# This is some experimental code, don't know if I'll use it or not

class ViewDefinitionMeta(type):
    def __new__(cls, name, bases, dic):
        # Divide methods from properties
        properties = {}
        methods = {}
        for k, v in dic.items():
            if  k.startswith('_') or callable(v):
                methods[k] = v
            else:
                properties[k] = v
        if '_doc_id' not in properties:
            properties['_doc_id'] = name
        # The real class only gets methods as part of it's definition
        new_class = super().__new__(cls, name, bases, methods)
        new_class._is_init = False
        # Properties become static instances of the class
        for k, v in properties.items():
            new_class.__dict__[k] = new_class(k, v)
        new_class._is_init = True
    

    def __call__(self, key, *args, **kwargs):
        # Class can never be initialized except by this metaclass, get
        # and call an exsiting instance instead
        if self._is_init:
            if key in self.__dict__:
                return self.__dict__[key](*args, **kwargs)
            else:
                raise KeyError(f"View {self.__name__}.{key} was not defined")
        else:
            return super().__call__(self, key, *args, **kwargs)


class ViewDefinition(metaclass=ViewDefinitionMeta):
    _database = None
    _wrapper = None
    def __init__(self, name, value):
        self.name = name
        self.presets = {}
        self.positional_args = (,)
        if isinstance(value, dict):
            self.presets = value
        elif isinstance(value, (tuple, list))
            if isinstance(value[0], (list, tuple)):
                self.positional_args[0]
                self.presets = value[1]
            else:
                self.positional_args = value
    
    def __call__(self, *args, **kwargs):
        if self._database is None:
            raise RuntimeError(f'No database was given to ViewDefinition {self._doc_id}')
        options = self.presets.copy()

        for k, v in zip(self.positional_args, args):
            options[k] = v
        options.update(kwargs)
        return self._database.view((self._doc_id, self.name), self._wrapper, **options)

