from pydantic import BaseModel
from datetime import date, time

class ScheduleCreate(BaseModel):
    user_id: int
    work_date: date
    start_time: time
    end_time: time

class ScheduleOut(ScheduleCreate):
    id: int

    class Config:
        from_attributes = True
