#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import json
import six

from django import forms
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .widgets import FormFieldWidget


class JSONField(models.TextField):
    """
    JSONField is a generic textfield that serializes/unserializes
    the data from our form fields
    """
    default_error_messages = {
        'invalid': _("'%s' is not a valid JSON string.")
    }
    description = "JSON object"

    def __init__(self, *args, **kwargs):
        self.dump_kwargs = kwargs.pop('dump_kwargs',
                                      {'cls': DjangoJSONEncoder})
        self.load_kwargs = kwargs.pop('load_kwargs', {})

        super(JSONField, self).__init__(*args, **kwargs)
        self.validate(self.get_default(), None)

    def validate(self, value, model_instance):
        if not self.null and value is None:
            raise ValidationError(self.error_messages['null'])
        try:
            self.get_prep_value(value)
        except ValueError:
            raise ValidationError(self.error_messages['invalid'] % value)

    def to_python(self, value):
        if isinstance(value, six.string_types):
            try:
                return json.loads(value, **self.load_kwargs)
            except ValueError:
                raise ValidationError(self.error_messages['invalid'] % value)

        return value

    def get_prep_value(self, value):
        if value is None:
            if not self.null and self.blank:
                return ""
            return None
        return json.dumps(value, **self.dump_kwargs)

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return None
        return json.loads(value, **self.decoder_kwargs)

    def get_db_prep_value(self, value, *args, **kwargs):
        if isinstance(value, six.string_types):
            return value

        return self.get_prep_value(value)

    def _get_val_from_obj(self, obj):
        return self.value_from_object(obj)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

    def value_from_object(self, obj):
        """
        Returns the value of this field in the given model instance.
        """
        if obj is not None:
            return getattr(obj, self.attname)
        else:
            return self.get_default()


class FormField(forms.MultiValueField):
    """The form field we can use in forms"""

    def __init__(self, form, **kwargs):
        import inspect
        if inspect.isclass(form) and issubclass(form, forms.Form):
            form_class = form
        elif callable(form):
            form_class = form()
            self.form = form_class()
        elif isinstance(form, six.string_types):
            from django.utils import module_loading
            if hasattr(module_loading, 'import_by_path'):
                form_class = module_loading.import_by_path(form)
            else:
                form_class = module_loading.import_string(form)
        self.form = form_class()

        # Set the widget and initial data
        kwargs['widget'] = FormFieldWidget([f for f in self.form])
        kwargs['initial'] = [f.field.initial for f in self.form]
        # The field it self should not be required, this allows us to
        # have optional fields in a sub form
        kwargs['required'] = False

        self.max_length = kwargs.pop('max_length', None)

        super(FormField, self).__init__(**kwargs)

        self.fields = [f.field for f in self.form]

    def compress(self, data_list):
        """
        Return the cleaned_data of the form, everything should already be valid
        """
        data = {}
        if data_list:
            return dict(
                (f.name, data_list[i]) for i, f in enumerate(self.form))
        return data

    def clean(self, value):
        """
        Call the form is_valid to ensure every value supplied is valid
        """
        if not value:
            raise ValidationError(
                'Error found in Form Field: Nothing to validate')

        data = dict((bf.name, value[i]) for i, bf in enumerate(self.form))
        self.form = form = self.form.__class__(data)
        if not form.is_valid():
            error_dict = list(form.errors.items())
            raise ValidationError([
                ValidationError(mark_safe('{} {}'.format(
                    k.title(), v)), code=k) for k, v in error_dict])

        # This call will ensure compress is called as expected.
        return super(FormField, self).clean(value)


class ModelFormField(JSONField):
    """The json backed field we can use in our models"""

    def __init__(self, *args, **kwargs):
        """
        This field needs to be nullable and blankable. The supplied form
        will provide the validation.
        """
        self.form = kwargs.pop('form', None)

        kwargs['null'] = True
        kwargs['blank'] = True

        super(ModelFormField, self).__init__(*args, **kwargs)

    def formfield(self, form_class=FormField, **kwargs):
        # Need to supply form to FormField
        return super(ModelFormField, self).formfield(form_class=form_class,
            form=self.form, **kwargs)
