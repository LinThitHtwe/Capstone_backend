# IoT-Only View – Class Diagram

This diagram shows only the entities/classes involved in **IoT monitoring and per-table display**:
- weight sensors attached to tables
- sensor readings for history/analytics
- tables that expose occupancy/free state
- LCD displays (entrance + per-table LCD)
- reservation session data used by the per-table LCD countdown and OTP check-in

--- 

## Mermaid class diagram

```mermaid
classDiagram
    direction TB

    class WeightSensor {
        +id: PK
        +name: str
        +location: str
        +calibration_weight_empty: float
        +calibration_weight_occupied: float
        +last_reading_at: datetime
        +is_available: bool
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
    }

    class ReservationSession {
        +id: PK
        +table: FK Table
        +start_time: datetime
        +end_time: datetime
        +status: Choice
        +otp: str
        +checked_in_at: datetime
    }

    class LCDDisplay {
        +id: PK
        +display_type: str  %% ENTRANCE or TABLE
        +table: FK Table (optional)
        +location: str
        +last_updated: datetime
        +get_entrance_count()
        +get_table_status()
        +get_countdown_minutes()
        +show_status_and_countdown()
    }

    %% ============ IoT relationships ============
    WeightSensor "1" -- "0..*" SensorReading : has readings
    WeightSensor "1" -- "1" Table : on table
    Table "1" -- "0..*" ReservationSession : active/previous sessions
    Table "1" -- "0..1" LCDDisplay : table LCD (for reservable tables)
    LCDDisplay ..> Table : entrance count (display_type=ENTRANCE)
    LCDDisplay ..> ReservationSession : countdown/status (display_type=TABLE)
```

