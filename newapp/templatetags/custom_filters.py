from django import template

register = template.Library() # если мы не зарегистрируем наши фильтры, то django никогда не узнает где именно их искать и фильтры потеряются :(



@register.filter(name='censor')
def censor(value):
    words = value.split()
    STOP_LIST = [
        'мат',
        'мат',
        'Dropbox',
    ]
    for w in words:
        if w in STOP_LIST:
            value = value.replace(w,'*' * len(w))
    return value