def getClassDict(par):
    z=dict()
    for cls in par.__mro__:
        if cls.__name__ == 'CHFSM':
            break
        z = {**cls.__dict__, **z}
    return z