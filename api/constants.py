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

# ``Table.status`` — app-defined integers for map / booking UX.
TABLE_STATUS_FREE = 1
TABLE_STATUS_OCCUPIED = 2
TABLE_STATUS_RESERVED = 3

# User reservations: wall-clock in this zone (Django may use UTC; library hours are local).
LIBRARY_RESERVATION_TZ = "Asia/Kuala_Lumpur"
RESERVATION_SLOT_MINUTES = 30
RESERVATION_DAY_START_HOUR = 9
RESERVATION_DAY_END_HOUR = 18
RESERVATION_MAX_MINUTES_PER_USER_PER_DAY = 240  # 4 hours
