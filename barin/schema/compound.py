"""Schemas for compound types (Documents and Arrays)."""
from .base import Schema, Invalid, Missing


class Document(Schema):
    _msgs = dict(
        Schema._msgs,
        not_doc='Value must be a document',
        extra='Field has no validator')

    def __init__(
            self,
            fields=Missing,
            allow_extra=False,
            extra_validator=Missing,
            **kwargs):
        super(Document, self).__init__(**kwargs)
        if fields is Missing:
            fields = {}
        if extra_validator is not Missing:
            allow_extra = True
        self.fields = fields
        self.allow_extra = allow_extra
        self.extra_validator = extra_validator

    def to_py(self, value, state=None):
        state = 'to_py'
        return self._validate(value, state)

    def to_db(self, value, state=None):
        state = 'to_db'
        return self._validate(value, state)

    def _validate(self, value, state=None):
        if not isinstance(value, dict):
            raise Invalid(self._msgs['not_doc'], value)
        validated = {}
        errors = {}

        # Validate by explicitly specified fields
        for name, validator in self.fields.items():
            r_val = value.get(name, Missing)
            try:
                subval = getattr(validator, state)
                v_val = subval(r_val)
                validated[name] = v_val
            except Invalid as err:
                errors[name] = err

        # Validate unknown keys ('extra fields')
        for name, r_val in value.items():
            if name in self.fields:
                continue
            if not self.allow_extra:
                errors[name] = Invalid(self._msg['extra'], r_val)
            elif self.extra_validator:
                try:
                    subval = getattr(self.extra_validator, state)
                    v_val = subval(r_val)
                    validated[name] = v_val
                except Invalid as err:
                    errors[name] = err
            else:
                validated[name] = r_val

        if errors:
            raise Invalid('', value, document=errors)
        return validated


class Array(Schema):
    _msgs = dict(
        Schema._msgs,
        not_arr='Value must be an array')

    def __init__(
            self,
            validator=Missing,
            only_validate=Missing,
            **kwargs):
        super(Array, self).__init__(**kwargs)
        self.validator = validator
        if isinstance(only_validate, slice):
            only_validate = [only_validate]
        elif only_validate is Missing:
            only_validate = [slice(None)]
        self.only_validate = only_validate

    def to_py(self, value, state=None):
        state = 'to_py'
        return self._validate(value, state)

    def to_db(self, value, state=None):
        state = 'to_db'
        return self._validate(value, state)

    def _validate_indices(self, length):
        seen = set()
        for sl in self.only_validate:
            indices = xrange(*sl.indices(length))
            for ix in indices:
                if ix in seen:
                    continue
                yield ix
                seen.add(ix)

    def _validate(self, value, state=None):
        if not isinstance(value, list):
            raise Invalid(self._msgs['not_arr'], value)
        if self.validator is Missing:
            return value
        validated = list(value)
        errors = [None] * len(value)
        has_errors = False

        for ix in self._validate_indices(len(value)):
            r_val = value[ix]
            try:
                subval = getattr(self.validator, state)
                v_val = subval(r_val)
                validated[ix] = v_val
            except Invalid as err:
                errors[ix] = err
                has_errors = True

        if has_errors:
            raise Invalid('', value, array=errors)

        return validated