from django import template
from django.utils.safestring import mark_safe
from markdownx.utils import markdownify
import inflect
from datetime import date
register = template.Library()


@register.filter
def markdown(text):
    return mark_safe(markdownify(text))


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
    elif s == '-bronze':
        return rider.bronze
    else:
        return rider.medal


@register.filter(name='asstr')
def asStr(var):
    return str(var)


@register.filter(name='sufix')
def addSufix(var):
    p = inflect.engine()
    return p.ordinal(str(var))


@register.filter(name='age')
def calculateAge(born):
    if not born:
        return 'Unknown'
    else:
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
