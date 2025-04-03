from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


register = template.Library()

@register.filter(name='mul')
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def get_at_index(lista, index):
    return lista[index] 


@register.filter
def sum_property(items, property_name):
    total = 0
    for item in items:
        try:
            total += getattr(item, property_name)
        except AttributeError:
            pass
    return total

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''