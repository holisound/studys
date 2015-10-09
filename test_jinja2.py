#!/usr/bin/env python
from jinja2 import Template
from jinja2 import Environment, FileSystemLoader
import os
def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(
        loader=FileSystemLoader(
            os.path.join(os.path.dirname(__file__), 'templates')),
        extensions=extensions,
    )
    jinja_env.globals.update(globals)

    # jinja_env.update_template_context(context)
    return jinja_env.get_template(template_name).render(context)
# variable
variable = "{{ foo.bar }}"
variable_dict = {
    'foo':{'bar':1234},
    'join_list':[str(i) for i in xrange(10)],
    'title':'I am title',
    'name':'Edward',
    }

defined = '{{ abc is defined }}'
margin = "{% for item in range(10) -%} {{ item }}            {%- endfor %}"
escape = "{% for item in ['{{','{','}','}}'] %}{% endfor %}"
# =====================
# filters
# =====================
join = '{{ join_list|join(",")}}'

def main():
    tmp = Template(variable)
    tmp = Template(join)
    tmp = Template(defined)
    tmp = Template(margin)
    tmp = Template(escape)

    print render_template('base.html', **variable_dict)
if __name__ == '__main__':
    main()