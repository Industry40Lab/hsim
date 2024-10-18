from types import MethodType


def do(instance):
    def decorator(f):
        f = MethodType(f, instance)
        setattr(instance, '_do', f)
        return f
    return decorator

def on_entry(instance):
    def decorator(f):
        f = MethodType(f, instance)
        instance._entry_callbacks.append(f)
        return f
    return decorator

def on_exit(instance):
    def decorator(f):
        f = MethodType(f, instance)
        instance._exit_callbacks.append(f)
        return f
    return decorator

def on_interrupt(instance):
    def decorator(f):
        f = MethodType(f, instance)
        instance._interrupt_callbacks.append(f)
        return f
    return decorator

def trigger(instance):
    def decorator(f):
        f = MethodType(f, instance)
        instance._trigger = f
        return f
    return decorator

def action(instance):
    def decorator(f):
        f = MethodType(f, instance)
        instance._action = f
        return f
    return decorator