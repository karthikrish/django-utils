from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


register = template.Library()

def get_fields_for_formset(formset, fields):
    if fields is None:
        return formset.empty_form.visible_fields()
    else:
        return [
            f for f in formset.empty_form.visible_fields() \
                if f.name in fields.split(',')
        ]

@register.filter
def formset_empty_row(formset, fields=None):
    return render_to_string('djutils/formset-empty-row.html', {
        'formset': formset,
        'form': formset.empty_form,
        'fields': get_fields_for_formset(formset, fields),
    })

@register.filter
def formset_add_row(formset, colspan=None):
    if colspan is None:
        fields = formset.empty_form.visible_fields()
        colspan = len(fields) + 1 # add one for the 'remove' link
    
    return render_to_string('djutils/formset-add-row.html', {
        'formset': formset,
        'colspan': colspan,
    })

@register.filter
def formset_forms(formset, fields=None):
    fields = get_fields_for_formset(formset, fields)
    col_span = len(fields) + 1 # adding one for the 'remove' link
    
    return mark_safe(render_to_string('djutils/formset-forms.html', {
        'formset': formset,
        'fields': [f.name for f in fields],
        'col_span': col_span,
    }).strip())

@register.filter
def formset_header_row(formset, fields=None):
    return render_to_string('djutils/formset-header-row.html', {
        'formset': formset,
        'fields': get_fields_for_formset(formset, fields)
    })

@register.filter
def dynamic_formset(formset, fields=None):
    form_fields = get_fields_for_formset(formset, fields)
    col_span = len(form_fields) + 1 # adding one for the 'remove' link
    
    return render_to_string('djutils/formset-dynamic.html', {
        'formset': formset,
        'fields': fields,
        'col_span': col_span,
    })
