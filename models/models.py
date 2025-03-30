from pydantic import BaseModel, Field, ConfigDict, field_serializer, validator
from typing import List, Optional, Dict
from bson import ObjectId
from bson.int64 import Int64
from datetime import datetime

# Custom Int64 wrapper for Pydantic
class PyInt64(Int64):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.int_schema()

    @classmethod
    def validate(cls, v):
        if isinstance(v, (int, Int64)):
            return Int64(v)
        raise ValueError("Invalid Int64 value")

class UserModel(BaseModel):
    id: str = Field(alias="_id")
    username: str
    password_hash: str
    created_at: datetime
    last_login: Optional[datetime]

    @validator("id", pre=True)
    def convert_object_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AsteroidElementModel(BaseModel):
    name: str
    mass_kg: PyInt64
    number: int

    @field_serializer("mass_kg")
    def serialize_int64(self, value: PyInt64) -> int:
        return int(value)

class AsteroidModel(BaseModel):
    id: str = Field(alias="_id")
    spkid: int
    full_name: str
    pdes: str
    name: str
    neo: bool
    hazard: bool
    abs_magnitude: float
    diameter: float
    albedo: float
    diameter_sigma: float
    orbit_id: str
    moid: float
    moid_days: int
    mass: PyInt64
    value: PyInt64
    elements: List[AsteroidElementModel]

    @field_serializer("id")
    def serialize_objectid(self, value: ObjectId) -> str:
        return str(value)

    @field_serializer("mass", "value")
    def serialize_int64(self, value: PyInt64) -> int:
        return int(value)

    model_config = ConfigDict(arbitrary_types_allowed=True, json_encoders={ObjectId: str, PyInt64: int})

class ElementModel(BaseModel):
    id: str = Field(alias="_id")
    name: str
    appearance: Optional[str]
    atomic_mass: float
    boil: Optional[float]
    category: str
    density: Optional[float]
    discovered_by: Optional[str]
    melt: Optional[float]
    molar_heat: Optional[float]
    named_by: Optional[str]
    number: int
    period: int
    group: int
    phase: str
    source: Optional[str]
    bohr_model_image: Optional[str]
    bohr_model_3d: Optional[str]
    spectral_img: Optional[str]
    summary: str
    symbol: str
    xpos: int
    ypos: int
    wxpos: int
    wypos: int
    shells: List[int]
    electron_configuration: str
    electron_configuration_semantic: str
    electron_affinity: Optional[float]
    electronegativity_pauling: Optional[float]
    ionization_energies: List[float]
    cpk_hex: Optional[str] = Field(alias="cpk-hex")
    image: Optional[dict]
    block: str
    uses: List[str]
    classes: List[dict]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, PyInt64: int}

class EventModel(BaseModel):
    id: str = Field(alias="_id")
    name: str
    effect: dict
    probability: float
    target: str

    @validator("id", pre=True)
    def convert_object_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, PyInt64: int}

class MissionDay(BaseModel):
    day: int
    total_kg: PyInt64
    note: str
    events: List[dict] = []
    elements_mined: Optional[Dict[str, int]] = None  # Daily element breakdown
    daily_value: Optional[int] = None  # Daily value in $

    @field_serializer("total_kg")
    def serialize_int64(self, value: PyInt64) -> int:
        return int(value)

class MissionModel(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    company: str
    asteroid_full_name: str
    name: str
    travel_days_allocated: int
    mining_days_allocated: int
    total_duration_days: int
    scheduled_days: int
    budget: int
    status: int  # 0: in progress, 1: completed, 2: failed
    elements: List[AsteroidElementModel]
    cost: PyInt64
    revenue: PyInt64
    profit: PyInt64
    penalties: PyInt64
    investor_repayment: PyInt64 = Int64(0)
    previous_debt: int = 0
    travel_delays: int = 0
    ship_repair_cost: PyInt64 = Int64(0)
    yield_multiplier: float = 1.0
    travel_yield_mod: float = 1.0 
    revenue_multiplier: float = 1.0
    daily_summaries: List[MissionDay] = []
    events: List[dict] = []
    rocket_owned: bool = False
    target_yield_kg: PyInt64  # No default, set by ship capacity

    @validator("id", "user_id", pre=True)
    def convert_object_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

    @field_serializer("id", "user_id")
    def serialize_objectid(self, value: ObjectId) -> str:
        return str(value)

    @field_serializer("cost", "revenue", "profit", "penalties", "investor_repayment", "ship_repair_cost", "target_yield_kg")
    def serialize_int64(self, value: PyInt64) -> int:
        return int(value)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, PyInt64: int}

class ShipModel(BaseModel):
    id: str = Field(alias="_id")
    name: str
    user_id: str
    shield: int
    mining_power: int
    created: datetime
    days_in_service: int
    location: float
    mission: int
    hull: int
    cargo: List[dict]
    capacity: int
    active: bool

    @validator("id", "user_id", pre=True)
    def convert_object_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

    @field_serializer("id", "user_id")
    def serialize_objectid(self, value: ObjectId) -> str:
        return str(value)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, PyInt64: int}