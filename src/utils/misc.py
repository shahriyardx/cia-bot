def find(list, func):
    return next(filter(func, list), None)
