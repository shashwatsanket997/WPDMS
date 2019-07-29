from django import template
register = template.Library()

@register.simple_tag(name='add_attr')
def add_attr(field , *args, **kwargs):
    attrs = {}
    for key,value in kwargs.items():
        if key == 'placeholder':
            attrs[key] = 'Enter ' + str(value)
        else:
            attrs[key] = value
    
    return field.as_widget(attrs=attrs)

@register.filter(name='field_type')
def field_type(field):
    return field.field.widget.__class__.__name__