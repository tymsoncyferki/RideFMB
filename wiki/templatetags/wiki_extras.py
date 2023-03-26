from django import template

register = template.Library()


@register.filter(name="sub")
def sub(value, arg):
    return value - arg


@register.filter(name='times')
def times(number):
    return range(1, number+1)


@register.filter(name='years')
def yearIterate(year):
    return range(2023, year-1, -1)


@register.filter(name='asint')
def asInt(number):
    return int(number)


@register.filter(name='path')
def getPath(path):
    return path.split('/')[1]


@register.filter(name='label')
def makeLabel(s):
    return s[1].upper() + s[2:] + 's'


@register.filter(name='medal')
def printMedal(rider, s):
    if s == '-gold':
        return rider.gold
    elif s == '-silver':
        return rider.silver
    else:
        return rider.bronze
