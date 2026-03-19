# Database Diagrams (Normalization Comparison)

This section provides three database schemas to help explain normalization for the Library Table Reservation System described in the ERD.

1. **Unnormalized / Denormalized (0NF-ish)**: a single table stores user + table + sensor + LCD + session data, including a non-atomic repeating group.
2. **1NF (atomic fields, but redundant + partial dependencies remain)**: tables are separated, but some non-key attributes still depend only on part of a composite key.
3. **2NF (normalized)**: redundancy is removed by separating sensor/table/LCD entities; reservation keeps only what depends on the whole key.

The final schema (current ERD) corresponds to **2NF and also 3NF** in practical terms (because relationships are decomposed by entity responsibilities and reservation stores only keys + session attributes).

---

## 1) Unnormalized / Denormalized Diagram

```mermaid
erDiagram
    ReservationSessionDenorm {
        int reservation_id PK
        int user_id
        string user_email
        string user_name
        string user_role
        string table_number
        string table_type
        int library_floor
        bool is_reservable
        int weight_sensor_id
        decimal sensor_cal_empty
        decimal sensor_cal_occupied
        string lcd_display_type
        string lcd_location
        datetime start_time
        datetime end_time
        string status
        string otp
        datetime checked_in_at
        datetime reminder_email_sent_at
        datetime overstay_alerted_at
        string sensor_readings_text
    }
```

Why it is unnormalized:
- user/table/sensor/LCD information is duplicated inside one record
- `sensor_readings_text` represents repeating data in one field (violates 1NF)

---

## 2) 1NF Diagram (atomic, but partial dependencies exist)

```mermaid
erDiagram
    accounts_user {
        int user_id PK
        string email
        string name
        string role
        string student_id
    }

    tables_table {
        int table_id PK
        string table_number
        string table_type
        int library_floor
        bool is_reservable
        int weight_sensor_id
    }

    reservations_reservation_1nf {
        int user_id PK, FK
        int table_id PK, FK
        datetime start_time PK
        datetime end_time
        string status
        string otp
        datetime checked_in_at
        datetime reminder_email_sent_at
        datetime overstay_alerted_at
        %% Redundant attributes that depend only on table_id, not on the whole composite key:
        string table_number_copy
        string table_type_copy
        int library_floor_copy
        decimal sensor_cal_empty_copy
        decimal sensor_cal_occupied_copy
        string lcd_location_copy
    }

    accounts_user ||--o{ reservations_reservation_1nf : user_id
    tables_table ||--o{ reservations_reservation_1nf : table_id
```

Why it is 1NF but not 2NF:
- All columns are atomic (no repeating groups).
- However, in `reservations_reservation_1nf`, attributes like `table_type_copy` depend only on `table_id` (a subset of the composite key), not the full key (`user_id, table_id, start_time`).
- Therefore, it violates the intent of 2NF.

---

## 3) 2NF Diagram (normalized, matches the ERD)

```mermaid
erDiagram
    accounts_user {
        int id PK
        string email
        string password
        string name
        string role
        string student_id
        string phone
        bool is_staff
        bool is_active
        datetime date_joined
    }

    tables_weight_sensor {
        int id PK
        string name
        string location
        decimal calibration_weight_empty
        decimal calibration_weight_occupied
        datetime last_reading_at
        bool is_available
    }

    tables_sensor_reading {
        int id PK
        int weight_sensor_id FK
        decimal weight
        datetime recorded_at
        bool inferred_occupied
    }

    tables_table {
        int id PK
        string table_number
        int weight_sensor_id FK
        bool is_reservable
        string table_type
        int library_floor
        int position_x
        int position_y
        string label
        bool is_available
    }

    devices_lcd_display {
        int id PK
      string display_type
        int table_id FK
        string location
        datetime last_updated
    }

    reservations_reservation {
        int id PK
        int user_id FK
        int table_id FK
        datetime start_time
        datetime end_time
        string status
        string otp
        datetime created_at
        datetime checked_in_at
        datetime reminder_email_sent_at
        datetime overstay_alerted_at
    }

    accounts_user ||--o{ reservations_reservation : user_id
    tables_table ||--o{ reservations_reservation : table_id
    tables_weight_sensor ||--o{ tables_table : "1 sensor per table (1:1)"
    tables_weight_sensor ||--o{ tables_sensor_reading : weight_sensor_id
    devices_lcd_display ||--o{ tables_table : table_id
```

Why this is 2NF (and also 3NF):
- Reservation stores only keys (`user_id`, `table_id`) and reservation/session attributes (time, status, otp, reminders).
- Table/type/floor/capacity live in `tables_table` and calibration lives in `tables_weight_sensor`.
- LCD behaviour is represented by `devices_lcd_display` (entrance vs table) and references `tables_table` when needed.

---

## Which normalization is your current ERD?

Your current ERD schema is designed to satisfy **at least 2NF** (and in typical database practice also 3NF):
- There are separate tables for different responsibilities (User, Table, Sensor, SensorReading, LCD, Reservation).
- There is no repeating group stored as text/array inside a row.
- Non-key attributes depend on their appropriate entity keys rather than being duplicated inside the reservation session row.

