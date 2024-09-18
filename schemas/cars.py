from datetime import datetime
from typing import TypeAlias, Literal, Optional
import pydantic


CarStatus: TypeAlias = Literal['out', 'parked']
BillStatus: TypeAlias = Literal['sent', 'paid', 'not issued']


class CarInfo(pydantic.BaseModel):
    """Represents the information of a car.

        Attributes:
            car_plate (str): The license plate of the car.
            status (CarStatus): The current status of the car ('out' by default).
        """
    car_plate: str
    status: CarStatus = 'out'


class ParkingInfo(pydantic.BaseModel):
    """Represents parking information.

        Attributes:
            car (str): The license plate of the car.
            start_time (datetime): The start time of the parking session.
            end_time (Optional[datetime]): The end time of the parking session (optional).
        """
    car: str
    start_time: datetime
    end_time: Optional[datetime] = None


class ParkingInfoExt(ParkingInfo):
    """Extends ParkingInfo with additional billing information.

        Attributes:
            cost (Optional[float]): The cost of the parking session (optional).
            bill_id (Optional[int]): The identifier for the associated bill (optional).
            bill_status (BillStatus): The status of the bill ('not issued' by default).
        """
    cost: Optional[float] = None
    bill_id: Optional[int] = None
    bill_status: BillStatus = 'not issued'


class BillingInfo(pydantic.BaseModel):
    """Represents billing information for a user.

        Attributes:
            id (int): The unique identifier of the bill.
            username (str): The username of the user associated with the bill.
            cost (float): The total cost to be paid.
            history (ParkingInfo): The parking information associated with this bill.
            status (BillStatus): The status of the bill ('not issued' by default).
        """
    id: int
    username: str
    cost: float
    history: ParkingInfo
    status: BillStatus = 'not issued'


class MessageInfo(pydantic.BaseModel):
    """Represents a message related to billing or user status.

        Attributes:
            id (int): The unique identifier of the message.
            user_id (int): The unique identifier of the user related to the message.
            bill_id (int): The identifier of the bill related to the message.
            message (str): The message content.
            is_active (bool): Whether the message is active.
            is_ban (Optional[bool]): Whether the message indicates a ban (False by default).
        """
    model_config = {
        'from_attributes': True 
    }
    id: int
    user_id: int
    bill_id: int
    message: str
    is_active: bool
    is_ban: Optional[bool] = False


class ParkingLot(pydantic.BaseModel):
    """Represents a parking lot.

        Attributes:
            id (int): The unique identifier of the parking lot.
            car_id (Optional[int]): The identifier of the car parked in the lot (optional).
        """
    model_config = {
        'from_attributes': True
    }

    id: int
    car_id: Optional[int] = None
