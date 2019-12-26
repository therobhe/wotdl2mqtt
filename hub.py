import importlib


IMPLEMENTATION_PATH = 'wot_api.models'
print('hub imported')

PERSISTENCE = {}
INIT_FUNCTION_NAME = 'init'


def invoke_implementation(function_name, params, kwargs, device):
    print('INVOKE IMPLEMENTATION REACHED')
#    print('TRANSMITTED PARAMETER: ' + str(function_name) + str(params) + str(kwargs) + str(device))

    import_path = IMPLEMENTATION_PATH + '.' + device

#    print('IMPORT PATH: ' + str(import_path))

    implementation_spec = importlib.util.find_spec(import_path)

#    print('IMPLEMENTATION SPEC: ' + str(implementation_spec))

    found = implementation_spec is not None

    if found:

#        print('FOUND:')

        implementation = importlib.import_module(import_path)

#        print(str(implementation))

        if hasattr(implementation, INIT_FUNCTION_NAME):
            plugin_init_function = getattr(implementation, INIT_FUNCTION_NAME)
            plugin_init_function()
        if not hasattr(implementation, function_name):
            return 'Implementation required for %s of device %s' % (function_name, device)
        method = getattr(implementation, function_name)

        if 'body' in kwargs:
            body = kwargs['body']
            for param in params:
                if param not in kwargs:
                    kwargs[param] = body[param]
            kwargs.pop('body')

        if len(kwargs) > 0:
            return method(**kwargs)
        else:
            return method()
    else:
        return 'Implementation required for device %s' % device
