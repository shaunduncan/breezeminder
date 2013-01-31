import importlib
import os


def _camelize(value):
    parts = value.split('_')
    parts = map(lambda x: x.capitalize(), parts)
    return ''.join(parts)


def install_breezeminder_commands(manager):
    """
    A really nasty automagic way to discover command files in
    breezeminder.management.commands. The name of the file, <name>.py
    determines the command line name. The name of the python class for the
    command should be camel-cased version of <name>.py
    """

    modules = [ x for x in os.listdir(__path__[0])\
            if not (x.startswith('__') or x.endswith('pyc'))]
    modules = map(lambda x: x.replace('.py', ''), modules)

    for name in modules:
        module = importlib.import_module('.'.join([__package__, name]))
        classname = _camelize(name)
        klass = getattr(module, classname)

        if klass:
            manager.add_command(name, klass())
