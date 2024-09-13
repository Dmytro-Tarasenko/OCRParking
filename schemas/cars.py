from datetime import datetime
from typing import TypeAlias, Literal, Optional
import pydantic


CarStatus: TypeAlias = Literal['out', 'parked']
BillStatus: TypeAlias = Literal['sent', 'paid', 'not issued']


class CarInfo(pydantic.BaseModel):
    car_plate: str
    status: CarStatus = 'out'


class ParkingInfo(pydantic.BaseModel):
    car: str
    start_time: datetime
    end_time: Optional[datetime] = None


class ParkingInfoExt(ParkingInfo):
    cost: Optional[float] = None
    bill_id: Optional[int] = None
    bill_status: BillStatus = 'not issued'


class BillingInfo(pydantic.BaseModel):
    username: str
    cost: float
    history: ParkingInfo
    status: BillStatus = 'not issued'
