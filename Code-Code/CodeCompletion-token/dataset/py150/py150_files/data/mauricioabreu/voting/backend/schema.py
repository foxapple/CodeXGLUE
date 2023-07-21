from marshmallow import Schema, fields, validate


class OptionSchema(Schema):
    id = fields.Integer(dump_only=True)
    description = fields.String(required=True)
    created_at = fields.DateTime(dump_only=True)


class VotingSchema(Schema):
    id = fields.Integer(dump_only=True)
    description = fields.String(required=True)
    created_at = fields.DateTime(dump_only=True)
    options = fields.Nested(
        OptionSchema, many=True, required=True,
        validate=validate.Length(min=2, error='Provide at least 2 options')
    )

    class Meta:
        ordered = True


class VoteSchema(Schema):
    option = fields.Integer(required=True)
