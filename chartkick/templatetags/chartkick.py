from __future__ import absolute_import

import json
import functools
import itertools

from django import template
from django.conf import settings


register = template.Library()


class ChartNode(template.Node):
    id = itertools.count()
    html = """
<div id="{id}" style="height: {height}; text-align: center; color: #999;
                      line-height: {height}; font-size: 14px;
                      font-family: Lucida Grande, Lucida Sans Unicode,
                      Verdana, Arial, Helvetica, sans-serif;">
    Loading...
</div>
<script>
//<![CDATA[
new Chartkick.{name}(document.getElementById("{id}"), {data}, {options});
//]]>
</script>
"""

    def __init__(self, name, variable, options=None):
        self.name = name
        self.variable = template.Variable(variable)
        self.options = options or {}

        for name, value in self.options.items():
            self.options[name] = template.Variable(value)

    def render(self, context):
        options = dict(id='chart-%s' % self.id.next(), height='300px')
        options.update(self.options)

        for name, value in options.items():
            if isinstance(value, template.Variable):
                options[name] = value.resolve(context)

        data = json.dumps(self.variable.resolve(context))
        return self.html.format(name=self.name, data=data,
                                options=json.dumps(options), **options)


def chart(name, parser, token):
    try:
        args = token.split_contents()
    except ValueError:
        msg = '%r statement requires at least one argument' % token.split_contents()[0]
        raise template.TemplateSyntaxError(msg)

    options = None
    if len(args) > 2:
        if args[2] != 'with':
            raise template.TemplateSyntaxError("Expected 'with' statement")

        try:
            options = dict(map(lambda x: x.split('='), args[3:]))
        except ValueError:
            raise template.TemplateSyntaxError('Invalid arguments')

    return ChartNode(name=name, variable=args[1], options=options)


register.tag('line_chart', functools.partial(chart, 'LineChart'))
register.tag('pie_chart', functools.partial(chart, 'PieChart'))
register.tag('column_chart', functools.partial(chart, 'ColumnChart'))


@register.simple_tag
def include_chartkick_scripts(token):
    if token.lower() == 'googlecharts' or not token:
        js = '<script src="http://www.google.com/jsapi"></script>'
    elif token.lower() == 'highcharts':
        js = '<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js"></script>\n\t'\
             '<script src="http://code.highcharts.com/highcharts.js"></script>\n\t'
    else:
        raise template.TemplateSyntaxError("Invalid argument: '%s'" % token)
    js += '<script src="{static}/chartkick.js"></script>'
    return js.format(static=settings.STATIC_URL)
