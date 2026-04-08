"""App-wide constants for roles and auth."""

ROLE_ADMIN = "admin"
# Legacy: older signups used ``member``; new signups use ``student`` explicitly.
ROLE_MEMBER = "member"
ROLE_STUDENT = "student"
ROLE_LECTURER = "lecturer"
ROLE_STAFF = "staff"
ROLE_VISITOR = "visitor"

PUBLIC_SIGNUP_ROLES = frozenset(
    {ROLE_STUDENT, ROLE_LECTURER, ROLE_STAFF, ROLE_VISITOR}
)
