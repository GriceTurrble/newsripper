from django import template

register = template.Library()


@register.filter(name="range")
def make_range(value):
    return range(value)


@register.filter()
def year_month_day(value):
    return "%d-%d-%d" % (value.year, value.month, value.day)
