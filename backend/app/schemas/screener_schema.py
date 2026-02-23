from pydantic import BaseModel
from typing import List, Literal, Union

AllowedOperators = Literal["<", ">", "<=", ">=", "="]
AllowedLogic = Literal["AND", "OR"]

class Condition(BaseModel):
    field: str
    operator: AllowedOperators
    value: Union[int, float]

class ScreenerRequest(BaseModel):
    conditions: List[Condition]
    logic: AllowedLogic