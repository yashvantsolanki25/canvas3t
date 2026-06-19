from __future__ import annotations

from marshmallow import EXCLUDE, Schema, fields, validate


class UserSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Email(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UserCreateSchema(UserSchema):
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8))


class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class PaintingSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    title = fields.Str(allow_none=True)
    filename = fields.Str(dump_only=True)
    thumbnail = fields.Str(dump_only=True)
    width = fields.Int(dump_only=True)
    height = fields.Int(dump_only=True)
    format = fields.Str(allow_none=True)
    tools_used = fields.Str(allow_none=True)
    tags = fields.Str(allow_none=True)
    folder = fields.Str(allow_none=True)
    is_public = fields.Bool(allow_none=True)
    prefix = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    image_url = fields.Str(dump_only=True)
    thumbnail_url = fields.Str(dump_only=True)

