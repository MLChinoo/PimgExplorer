from pydantic import BaseModel
from typing import List, Optional


class Layer(BaseModel):
    layer_id: int
    layer_type: Optional[int]
    diff_id: Optional[int] = None
    name: str
    type: Optional[int]
    width: int
    height: int
    left: int
    top: int
    opacity: int
    visible: int

class PIMGJson(BaseModel):
    width: int
    height: int
    layers: List[Layer]
