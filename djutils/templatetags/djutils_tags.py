import re

from django import template
from django.db.models.loading import get_model
from django.db.models.query import QuerySet
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from djutils.constants import SYNTAX_HIGHLIGHT_RE
from djutils.db.managers import PublishedManager
from djutils.utils.highlighter import highlight


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

@register.filter
def popular_tags(ctype, limit=None):
    model = get_model(*ctype.split('.', 1))
    tag_qs = model.tags.most_common()
    if limit:
        tag_qs = tag_qs[:int(limit)]
    return tag_qs

def _model_to_queryset(model):
    if isinstance(model, QuerySet):
        return model
    
    if isinstance(model, basestring):
        model = get_model(*model.split('.'))
    
    if isinstance(model._default_manager, PublishedManager):
        return model._default_manager.published()
    else:
        return model._default_manager.all()

@register.filter
def latest(model_or_qs, date_field='id'):
    return _model_to_queryset(model_or_qs).order_by('-%s' % date_field)

@register.filter
def alpha(model, field='title'):
    return _model_to_queryset(model).order_by('%s' % field)

@register.filter
def call_manager(model_or_obj, method):
    # load up the model if we were given a string
    if isinstance(model_or_obj, basestring):
        model_or_obj = get_model(*model_or_obj.split('.'))

    # figure out the manager to query
    if isinstance(model_or_obj, QuerySet):
        manager = model_or_obj
    else:
        manager = model_or_obj._default_manager

    return getattr(manager, method)()

@register.filter
def syntax_highlight(text):
    """
    Automatically syntax-highlight text between
    &lt;code&gt; tags.
    
    Usage:
    {{ entry.body|syntax_highlight|linebreaks }}
    """
    return mark_safe(re.sub(
        SYNTAX_HIGHLIGHT_RE,
        syntax_highlight_callback,
        text
    ))

def syntax_highlight_callback(match_object):
    data = match_object.group(4)
    data = data.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
    return highlight(data)
