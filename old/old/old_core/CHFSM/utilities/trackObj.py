def trackObj(sm):
    entity = None
    items = []
    if hasattr(sm,'var'):
        if hasattr(sm.var,'entity'):
            entity = sm.var.entity
    if hasattr(sm,'Store'):
        pass
    elif hasattr(sm,'Store'):
        pass
    return entity, items