from django.db import models

from django.utils.translation import ugettext_lazy as _


class CreationDateTimeField(models.DateTimeField):
    """ CreationDateTimeField

    By default, sets editable=False, blank=True, auto_now_add=True
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('editable', False)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('auto_now_add', True)
        models.DateTimeField.__init__(self, *args, **kwargs)

    def get_internal_type(self):
        return "DateTimeField"

    def deconstruct(self):
        name, path, args, kwargs = super(
            CreationDateTimeField, self).deconstruct()
        if self.editable is not False:
            kwargs['editable'] = True
        if self.blank is not True:
            kwargs['blank'] = False
        if self.auto_now_add is not False:
            kwargs['auto_now_add'] = True
        return name, path, args, kwargs


class ModificationDateTimeField(CreationDateTimeField):
    """ ModificationDateTimeField

    By default, sets editable=False, blank=True, auto_now=True

    Sets value to now every time the object is saved.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_now', True)
        models.DateTimeField.__init__(self, *args, **kwargs)

    def get_internal_type(self):
        return "DateTimeField"

    def deconstruct(self):
        name, path, args, kwargs = super(
            ModificationDateTimeField, self).deconstruct()
        if self.auto_now is not False:
            kwargs['auto_now'] = True
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        if not getattr(model_instance, 'update_modified', True):
            return model_instance.modified
        return super(ModificationDateTimeField, self).pre_save(model_instance, add)


class TimeStampedModel(models.Model):
    """ TimeStampedModel
    An abstract base class model that provides self-managed "created" and
    "modified" fields.
    """
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))

    def save(self, **kwargs):
        self.update_modified = kwargs.pop(
            'update_modified', getattr(self, 'update_modified', True))
        super(TimeStampedModel, self).save(**kwargs)

    class Meta:
        get_latest_by = 'modified'
        ordering = ('-modified', '-created',)
        abstract = True
