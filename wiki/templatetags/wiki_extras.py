from django import template

register = template.Library()


@register.filter(name="sub")
def sub(value, arg):
    return value - arg


@register.filter(name='times')
def times(number):
    return range(1, number+1)