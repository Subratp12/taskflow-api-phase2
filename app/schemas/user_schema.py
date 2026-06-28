"""
TaskFlow API — User Schemas
─────────────────────────────────────────────────────────────────────────────
Marshmallow schemas for input validation and output serialization.

Rule: EVERY piece of data entering the API goes through a schema.
      Raw request JSON is NEVER trusted directly.

Schemas used:
    UserRegistrationSchema  ← POST /auth/register
    UserLoginSchema         ← POST /auth/login
    UserUpdateSchema        ← PUT  /users/me
    UserResponseSchema      ← All user responses (never exposes password_hash)
    UserPublicSchema        ← Minimal user info embedded in other responses
"""

import re

from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    validate,
    validates,
    validates_schema,
)


class UserRegistrationSchema(Schema):
    """Validates new user registration payload."""

    class Meta:
        unknown = EXCLUDE  # Silently ignore unexpected fields

    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=50, error='Username must be 3–50 characters'),
            validate.Regexp(
                r'^[a-zA-Z0-9_]+$',
                error='Username may only contain letters, numbers, and underscores',
            ),
        ],
    )
    email = fields.Email(
        required=True,
        validate=validate.Length(max=255),
    )
    password = fields.Str(
        required=True,
        load_only=True,   # Never serialize back
        validate=validate.Length(min=8, max=128, error='Password must be 8–128 characters'),
    )
    first_name = fields.Str(
        load_default=None,
        validate=validate.Length(max=50),
    )
    last_name = fields.Str(
        load_default=None,
        validate=validate.Length(max=50),
    )

    @validates('password')
    def validate_password_strength(self, value: str) -> None:
        errors = []
        if not re.search(r'[A-Z]', value):
            errors.append('at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            errors.append('at least one lowercase letter')
        if not re.search(r'\d', value):
            errors.append('at least one digit')
        if errors:
            raise ValidationError(f'Password must contain {", ".join(errors)}')

    @validates('email')
    def validate_email_lower(self, value: str) -> None:
        # Pre-normalise: emails are case-insensitive
        return value.lower().strip()


class UserLoginSchema(Schema):
    """Validates login credentials."""

    class Meta:
        unknown = EXCLUDE

    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class UserUpdateSchema(Schema):
    """Validates profile update payload. All fields optional."""

    class Meta:
        unknown = EXCLUDE

    first_name = fields.Str(validate=validate.Length(max=50), load_default=None)
    last_name = fields.Str(validate=validate.Length(max=50), load_default=None)
    email = fields.Email(validate=validate.Length(max=255), load_default=None)

    # Password change requires both current and new password
    current_password = fields.Str(load_only=True, load_default=None)
    new_password = fields.Str(
        load_only=True,
        load_default=None,
        validate=validate.Length(min=8, max=128),
    )

    @validates_schema
    def validate_password_change(self, data: dict, **kwargs) -> None:
        """If changing password, both current and new must be provided."""
        has_current = bool(data.get('current_password'))
        has_new = bool(data.get('new_password'))
        if has_current != has_new:
            raise ValidationError(
                'Both current_password and new_password are required to change password'
            )


class UserAdminUpdateSchema(Schema):
    """Admin-only: update user role or active status."""

    class Meta:
        unknown = EXCLUDE

    role = fields.Str(
        load_default=None,
        validate=validate.OneOf(['admin', 'manager', 'developer']),
    )
    is_active = fields.Bool(load_default=None)


# ── Response Schemas (Output) ──────────────────────────────────────────────────

class UserResponseSchema(Schema):
    """Full user response — safe to return to the authenticated user."""

    id = fields.UUID(dump_only=True)
    username = fields.Str(dump_only=True)
    email = fields.Str(dump_only=True)
    role = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    first_name = fields.Str(dump_only=True, allow_none=True)
    last_name = fields.Str(dump_only=True, allow_none=True)
    full_name = fields.Str(dump_only=True)
    last_login_at = fields.DateTime(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UserPublicSchema(Schema):
    """
    Minimal user info — embedded in tasks, comments, project member lists.
    Never includes email in public contexts.
    """

    id = fields.UUID(dump_only=True)
    username = fields.Str(dump_only=True)
    full_name = fields.Str(dump_only=True)
    role = fields.Str(dump_only=True)


# ── Schema Instances (reused across routes) ────────────────────────────────────
user_registration_schema = UserRegistrationSchema()
user_login_schema = UserLoginSchema()
user_update_schema = UserUpdateSchema()
user_admin_update_schema = UserAdminUpdateSchema()
user_response_schema = UserResponseSchema()
users_response_schema = UserResponseSchema(many=True)
user_public_schema = UserPublicSchema()
