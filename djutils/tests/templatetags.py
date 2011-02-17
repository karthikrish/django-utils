from django import forms
from django.forms.formsets import formset_factory

from djutils.templatetags.djutils_tags import (
    formset_empty_row, formset_add_row, formset_forms, formset_header_row,
    dynamic_formset,
)
from djutils.test import TestCase


class TestForm(forms.Form):
    name = forms.CharField()
    choice = forms.ChoiceField(choices=(
        (1, 'One'),
        (2, 'Two'),
    ))
    invisible = forms.CharField(widget=forms.HiddenInput())


class DjangoUtilsTemplateTagTestCase(TestCase):
    def setUp(self):
        self.FormSet = formset_factory(TestForm)
        self.formset = self.FormSet()
    
    def test_formset_empty_row(self):
        self.assertEqual(self.formset.prefix, 'form')
        
        rendered = formset_empty_row(self.formset)
        
        self.assertEqual(rendered.splitlines(), [
            '<tr class="empty-row form">',
            '  <td><input type="text" name="form-__prefix__-name" id="id_form-__prefix__-name" /></td><td><select name="form-__prefix__-choice" id="id_form-__prefix__-choice">',
            '<option value="1">One</option>',
            '<option value="2">Two</option>',
            '</select></td>',
            '  <td><a href="javascript:void(0)" class="form-delete-row">Remove</a></td>',
            '</tr>'
        ])
        
        rendered = formset_empty_row(self.formset, 'name')
        self.assertEqual(rendered.splitlines(), [
            '<tr class="empty-row form">',
            '  <td><input type="text" name="form-__prefix__-name" id="id_form-__prefix__-name" /></td>',
            '  <td><a href="javascript:void(0)" class="form-delete-row">Remove</a></td>',
            '</tr>'
        ])
    
    def test_formset_add_row(self):
        rendered = formset_add_row(self.formset)
        
        self.assertEqual(rendered.splitlines(), [
            '<tr id="form-add-row">',
            '  <td colspan="3"><a href="javascript:void(0)" class="form-add-row">Add row</a></td>',
            '</tr>'
        ])
    
    def test_formset_forms(self):
        rendered = formset_forms(self.formset)
        self.assertEqual(rendered.splitlines(), [
            '<tr class="dynamic-form form">',
            '    <td><input type="text" name="form-0-name" id="id_form-0-name" /></td><td><select name="form-0-choice" id="id_form-0-choice">',
            '<option value="1">One</option>',
            '<option value="2">Two</option>',
            '</select></td>',
            '    ',
            '  </tr>',
        ])
        
        rendered = formset_forms(self.formset, 'name')
        self.assertEqual(rendered.splitlines(), [
            '<tr class="dynamic-form form">',
            '    <td><input type="text" name="form-0-name" id="id_form-0-name" /></td>',
            '    ',
            '  </tr>',
        ])
    
    def test_formset_header_row(self):
        rendered = formset_header_row(self.formset)
        self.assertEqual(rendered.splitlines(), [
            '<thead><tr class="header-row form">',
            '  <th>Name</th><th>Choice</th>',
            '</tr></thead>'
        ])
        
        rendered = formset_header_row(self.formset, 'name')
        self.assertEqual(rendered.splitlines(), [
            '<thead><tr class="header-row form">',
            '  <th>Name</th>',
            '</tr></thead>'
        ])
    
    def test_dynamic_formset(self):
        rendered = dynamic_formset(self.formset)
        self.assertEqual(rendered.splitlines(), [
            '',
            '<thead><tr class="header-row form">',
            '  <th>Name</th><th>Choice</th>',
            '</tr></thead>',
            '',
            '<tr class="empty-row form">',
            '  <td><input type="text" name="form-__prefix__-name" id="id_form-__prefix__-name" /></td><td><select name="form-__prefix__-choice" id="id_form-__prefix__-choice">',
            '<option value="1">One</option>',
            '<option value="2">Two</option>',
            '</select></td>',
            '  <td><a href="javascript:void(0)" class="form-delete-row">Remove</a></td>',
            '</tr>',
            '',
            '<tr class="dynamic-form form">',
            '    <td><input type="text" name="form-0-name" id="id_form-0-name" /></td><td><select name="form-0-choice" id="id_form-0-choice">',
            '<option value="1">One</option>',
            '<option value="2">Two</option>',
            '</select></td>',
            '    ',
            '  </tr>',
            '<tr id="form-add-row">',
            '  <td colspan="3"><a href="javascript:void(0)" class="form-add-row">Add row</a></td>',
            '</tr>',
            ''
        ])
