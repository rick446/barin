"""Shorthand compiler for schemas."""
from datetime import datetime


def compile_schema(s, **options):
    from barin import schema as S
    if s is None:
        return S.Anything()
    if isinstance(s, S.Validator):
        return s
    elif isinstance(s, list):
        if len(s) == 1:
            schema = compile_schema(s[0])
            return S.Array(validator=schema, **options)
        elif len(s) == 0:
            return S.Array(**options)
        else:
            raise S.Invalid('Invalid schema {}'.format(s))
    elif isinstance(s, dict):
        fields = dict(
            (name, compile_schema(value))
            for name, value in s.items())
        extra_validator = fields.pop(str, S.Missing)
        return S.Document(
            fields=fields,
            extra_validator=extra_validator,
            **options)
    elif issubclass(s, (int, long)):
        return S.Integer(**options)
    elif issubclass(s, datetime):
        return S.DateTime(**options)
    elif issubclass(s, float):
        return S.Float(**options)
    elif issubclass(s, basestring):
        return S.Unicode(**options)
    else:
        raise S.Invalid('Invalid schema {}'.format(s))