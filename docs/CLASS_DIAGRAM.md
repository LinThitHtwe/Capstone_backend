# Library Table Reservation System – Class Diagram

Entrance LCD (available-seat count), reservable vs walk-in tables, table type (e.g. 1-person, 4-person), per-table LCD (status + countdown), OTP keypad check-in, librarian overstay alerts, email reminder before session end, and virtual map for layout and booking.

---

## Mermaid class diagram

```mermaid
classDiagram
    direction TB

    %% ============ Authentication ============
    class User {
        <<Django AbstractUser>>
        +id: PK
        +email: str
        +password: str
        +name: str
        +role: str
        +student_id: str
        +phone: str
        +is_staff: bool
        +is_active: bool
        +date_joined: datetime
        +is_student() bool
        +is_staff_role() bool
        +get_reservations()
    }

    %% ============ Physical / IoT ============
    class WeightSensor {
        +id: PK
        +name: str
        +location: str
        +calibration_weight_empty: float
        +calibration_weight_occupied: float
        +last_reading_at: datetime
        +is_available: bool
        +get_current_state()
        +update_reading(weight)
    }

    class SensorReading {
        +id: PK
        +weight_sensor: FK WeightSensor
        +weight: float
        +recorded_at: datetime
        +inferred_occupied: bool
    }

    class Table {
        +id: PK
        +table_number: str
        +weight_sensor: OneToOne WeightSensor
        +is_reservable: bool
        +table_type: str
        +library_floor: int
        +position_x: int
        +position_y: int
        +label: str
        +is_available: bool
        +get_current_availability()
        +is_available_to_book(slot)
    }

    %% ============ Reservations ============
    class Reservation {
        +id: PK
        +user: FK User
        +table: FK Table
        +start_time: datetime
        +end_time: datetime
        +status: Choice
        +otp: str
        +created_at: datetime
        +checked_in_at: datetime
        +reminder_email_sent_at: datetime
        +overstay_alerted_at: datetime
        +cancel()
        +mark_did_not_come()
        +check_in_with_otp(otp)
        +mark_success()
    }

    %% ============ Displays ============
    class LCDDisplay {
        <<Service/Device>>
        +id: PK
        +display_type: str
        +table: FK Table (optional)
        +location: str
        +last_updated: datetime
        +get_entrance_count()
        +get_table_status()
        +get_countdown_minutes()
        +show_status_and_countdown()
    }

    %% ============ Relationships ============
    WeightSensor "1" -- "0..*" SensorReading : has readings
    WeightSensor "1" -- "1" Table : on table
    User "1" -- "*" Reservation : has
    Table "1" -- "*" Reservation : has
    Table "1" -- "0..1" LCDDisplay : table LCD
    LCDDisplay ..> Table : entrance reads total available count (display_type=ENTRANCE)
    LCDDisplay ..> Reservation : table LCD reads active reservation for status/countdown (display_type=TABLE)
```

---

## Relationship summary

| From         | To             | Relationship | Description                                        |
|-------------|----------------|-------------|----------------------------------------------------|
| User        | Reservation    | 1 : N       | A user has many reservations (students in app logic) |
| Table       | Reservation    | 1 : N       | A table has many reservations (only if is_reservable) |
| Table       | LCDDisplay     | 0..1 : 1    | Reservable table may have one table LCD (status, countdown) |
| Table       | WeightSensor   | 1 : 1       | Each table has one sensor (sensor on table)        |
| WeightSensor| SensorReading  | 1 : N       | Sensor has many readings (for analysis)           |
| LCDDisplay  | Table          | uses        | Entrance LCD reads total available count; table LCD reads that table’s status |
| LCDDisplay  | Reservation    | uses        | Table LCD derives countdown/status from active reservation |

---

## Enumerations / Choices

**Table:**  
- **is_reservable:** true = book in advance, false = walk-in only.  
- **table_type:** e.g. SINGLE (1-person), DOUBLE (2-person), QUAD (4-person).

**LCDDisplay.display_type:** `ENTRANCE` (at library entrance) | `TABLE` (at a reservable table).

**Reservation status:**  
- `PENDING` – created, not yet checked in  
- `SUCCESS` – user checked in with OTP / used table  
- `DID_NOT_COME` – no show  
- `CANCELLED` – cancelled by user or librarian  
- `EXPIRED` – time window passed without check-in  

---

## Behaviour summary

- **Entrance LCD:** Shows total available seats (all tables where is_available = true).  
- **Table LCD (reservable):** Shows status (reserved, available, etc.) and, in last 30 minutes of session, countdown; student sees reminder before session expires.  
- **OTP keypad:** At reservable table, user enters OTP; system verifies and sets checked_in_at (confirms booker is at table).  
- **Librarian:** Gets alert when student sits beyond booking time (overstay); overstay_alerted_at used so alert is sent once.  
- **Email:** Reminder sent to student before session expires; reminder_email_sent_at avoids duplicate emails.  
- **Virtual map:** Uses Table (position_x, position_y, library_floor, is_reservable, is_available). Shows free/occupied and which reservable tables are available to book; student clicks reservable table to create reservation.
