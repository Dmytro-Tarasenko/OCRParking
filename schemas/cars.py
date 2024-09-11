from datetime import datetime
from typing import TypeAlias, Literal, Optional, Any
import pydantic


CarStatus: TypeAlias = Literal['out', 'parked']


class CarInfo(pydantic.BaseModel):
    car_plate: str
    status: CarStatus = 'out'


class ParkingInfo(pydantic.BaseModel):
    car: str
    start_time: datetime
    end_time: Optional[datetime] = None


class BillingInfo(pydantic.BaseModel):
    username: str
    cost: float
    history: ParkingInfo
    is_paid: bool = False
