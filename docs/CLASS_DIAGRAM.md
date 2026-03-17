# Library Table Reservation System – Class Diagram

Django-based IoT system: weight sensors on **tables** (detection by table, not seat) → table availability, LCD display, web map & reservations, student registration & history, admin management & analysis. No library zones; each table has one sensor.

---

## Mermaid class diagram

```mermaid
classDiagram
    direction TB

    %% ============ Authentication & Users ============
    class User {
        <<Django AbstractUser>>
        +id: PK
        +email: str
        +password: str
        +first_name: str
        +last_name: str
        +is_staff: bool
        +is_active: bool
        +date_joined: datetime
        +is_student() bool
        +is_admin() bool
    }

    class Student {
        <<Profile>>
        +id: PK
        +user: OneToOne User
        +student_id: str
        +email: str
        +phone: str
        +created_at: datetime
        +get_reservations()
        +get_reservation_history()
    }

    %% ============ Physical / IoT Layer (sensor on table) ============
    class WeightSensor {
        +id: PK
        +sensor_id: str
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
        +sensor: FK WeightSensor
        +weight: float
        +recorded_at: datetime
        +inferred_occupied: bool
    }

    class Table {
        +id: PK
        +table_number: str
        +sensor: OneToOne WeightSensor
        +position_x: int
        +position_y: int
        +label: str
        +is_available: bool
        +get_current_availability()
    }

    %% ============ Reservations ============
    class Reservation {
        +id: PK
        +student: FK Student
        +table: FK Table
        +start_time: datetime
        +end_time: datetime
        +status: Choice
        +created_at: datetime
        +checked_in_at: datetime
        +cancel()
        +mark_did_not_come()
        +mark_success()
    }

    %% ============ Display / External ============
    class LCDDisplay {
        <<Service/Device>>
        +id: PK
        +device_id: str
        +location: str
        +last_updated: datetime
        +refresh_available_count()
        +get_display_data()
    }

    %% ============ Relationships ============
    User "1" -- "1" Student : has profile
    WeightSensor "1" -- "0..*" SensorReading : has readings
    WeightSensor "1" -- "1" Table : on table
    Student "1" -- "*" Reservation : has
    Table "1" -- "*" Reservation : has
    LCDDisplay ..> Table : reads available count
```

---

## Relationship summary

| From         | To             | Relationship | Description                                        |
|-------------|----------------|-------------|----------------------------------------------------|
| User        | Student        | 1 : 1       | One user account, one student profile              |
| Student     | Reservation    | 1 : N       | A student has many reservations                    |
| Table       | Reservation    | 1 : N       | A table has many reservations (over time)         |
| Table       | WeightSensor   | 1 : 1       | Each table has one sensor (sensor on table)        |
| WeightSensor| SensorReading  | 1 : N       | Sensor has many readings (for analysis)           |
| LCDDisplay  | Table          | uses        | Reads availability to show “tables available”     |

---

## Enumerations / Choices

**Reservation status (Django `TextChoices`):**

- `PENDING` – created, not yet used  
- `SUCCESS` – student checked in / used table  
- `DID_NOT_COME` – no show  
- `CANCELLED` – cancelled by student or admin  
- `EXPIRED` – time window passed without check-in  

---

## Django app suggestion

- **`accounts`** – `User`, `Student`  
- **`tables`** – `Table`, `WeightSensor`, `SensorReading`  
- **`reservations`** – `Reservation`  
- **`devices`** (optional) – `LCDDisplay` if you store device config in DB  


---

## PlantUML (for draw.io / PlantUML tools)

Save as `CLASS_DIAGRAM.puml` and open in [PlantUML](https://www.plantuml.com/plantuml) or import into draw.io.

```plantuml
@startuml Library Table Reservation - Class Diagram
skinparam classAttributeIconSize 0
skinparam classFontStyle bold

package "Authentication" {
  class User {
    __ Django AbstractUser __
    + id : PK
    + email : str
    + password : str
    + first_name : str
    + last_name : str
    + is_staff : bool
    + is_active : bool
    + date_joined : datetime
    + is_student() : bool
    + is_admin() : bool
  }
  class Student {
    __ Profile __
    + id : PK
    + user : OneToOne User
    + student_id : str
    + email : str
    + phone : str
    + created_at : datetime
    + get_reservations() : QuerySet
    + get_reservation_history() : QuerySet
  }
}

package "IoT & Tables (sensor on table)" {
  class WeightSensor {
    + id : PK
    + sensor_id : str
    + name : str
    + location : str
    + calibration_weight_empty : float
    + calibration_weight_occupied : float
    + last_reading_at : datetime
    + is_available : bool
    + get_current_state() : bool
    + update_reading(weight : float) : void
  }
  class SensorReading {
    + id : PK
    + sensor : FK WeightSensor
    + weight : float
    + recorded_at : datetime
    + inferred_occupied : bool
  }
  class Table {
    + id : PK
    + table_number : str
    + sensor : OneToOne WeightSensor
    + position_x : int
    + position_y : int
    + label : str
    + is_available : bool
    + get_current_availability() : bool
  }
}

package "Reservations" {
  enum ReservationStatus {
    PENDING
    SUCCESS
    DID_NOT_COME
    CANCELLED
    EXPIRED
  }
  class Reservation {
    + id : PK
    + student : FK Student
    + table : FK Table
    + start_time : datetime
    + end_time : datetime
    + status : ReservationStatus
    + created_at : datetime
    + checked_in_at : datetime
    + cancel() : void
    + mark_did_not_come() : void
    + mark_success() : void
  }
}

package "Display" {
  class LCDDisplay {
    << Service/Device >>
    + id : PK
    + device_id : str
    + location : str
    + last_updated : datetime
    + refresh_available_count() : int
    + get_display_data() : dict
  }
}

User "1" -- "1" Student : has profile
WeightSensor "1" -- "0..*" SensorReading : has readings
WeightSensor "1" -- "1" Table : on table
Student "1" -- "*" Reservation : has
Table "1" -- "*" Reservation : has
Reservation ..> ReservationStatus : uses
LCDDisplay ..> Table : reads available count

@enduml
```

