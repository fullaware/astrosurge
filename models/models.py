from pydantic import BaseModel, Field, ConfigDict, field_serializer, validator
from typing import List, Optional, Dict
from bson import ObjectId
from bson.int64 import Int64
from datetime import datetime

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

class User(BaseModel):
    id: str = Field(alias="_id")
    username: str
    email: Optional[str] = None
    hashed_password: str
    company_name: str = "Unnamed Company"
    bank: PyInt64 = PyInt64(0)
    loan_count: int = 0
    current_loan: PyInt64 = PyInt64(0)
    max_overrun_days: int = 10
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    @validator("id", pre=True)
    def convert_object_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

    @validator("bank", "current_loan", pre=True)
    def coerce_to_int64(cls, v):
        if v is None:
            return PyInt64(0)
        return PyInt64(int(v)) if isinstance(v, (int, float, str)) else v

    @field_serializer("bank", "current_loan")
    def serialize_int64(self, value: PyInt64) -> int:
        return int(value)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, Int64: int}

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    company_name: Optional[str] = "Unnamed Company"

class UserUpdate(BaseModel):
    company_name: Optional[str]
    email: Optional[str] = None
    max_overrun_days: Optional[int] = None

class MissionStart(BaseModel):
    asteroid_full_name: str
    ship_name: str
    travel_days: int

class Token(BaseModel):
    access_token: str
    token_type: str

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
    elements_mined: Optional[Dict[str, int]] = None
    daily_value: Optional[int] = None

    @field_serializer("total_kg")
    def serialize_int64(self, value: PyInt64) -> int:
        return int(value)

class MissionModel(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    company: str
    ship_name: str
    ship_id: Optional[str] = None
    asteroid_full_name: str
    name: str
    travel_days_allocated: int
    mining_days_allocated: int
    total_duration_days: int
    scheduled_days: int
    budget: int
    status: int
    elements: List[AsteroidElementModel]
    cost: int
    revenue: int
    profit: int
    penalties: int
    investor_repayment: int
    ship_repair_cost: int
    previous_debt: int
    events: List[dict]
    daily_summaries: List[dict]
    rocket_owned: bool
    yield_multiplier: float
    revenue_multiplier: float
    travel_yield_mod: float
    travel_delays: int
    target_yield_kg: Int64
    graph_html: Optional[str] = None
    confidence: Optional[float] = None
    predicted_profit_max: Optional[int] = None
    confidence_result: Optional[str] = None
    ship_location: Optional[float] = 0.0
    total_yield_kg: Optional[Int64] = Int64(0)
    days_into_mission: Optional[int] = 0
    days_left: Optional[int] = 0
    mission_cost: Optional[Int64] = Int64(0)
    mission_projection: Optional[int] = 0
    completed_at: Optional[datetime] = None  # Added for sorting

    @validator("id", "user_id", pre=True)
    def convert_object_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

    @validator("predicted_profit_max", "mission_projection", pre=True)
    def coerce_to_int(cls, v):
        if v is None:
            return None
        return int(float(v)) if isinstance(v, (float, str)) else v

    @validator("total_yield_kg", "mission_cost", "target_yield_kg", pre=True)
    def coerce_to_int64(cls, v):
        if v is None:
            return Int64(0)
        return Int64(int(v)) if isinstance(v, (int, float, str)) else v

    @field_serializer("id", "user_id")
    def serialize_objectid(self, value: ObjectId) -> str:
        return str(value)

    @field_serializer("cost", "revenue", "profit", "penalties", "investor_repayment", "ship_repair_cost", "target_yield_kg", "total_yield_kg", "mission_cost")
    def serialize_int64(self, value: PyInt64) -> int:
        return int(value)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, Int64: int}

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
    missions: List[str] = []

    @validator("id", "user_id", pre=True)
    def convert_object_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

    @field_serializer("id", "user_id")
    def serialize_objectid(self, value: ObjectId) -> str:
        return str(value)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, Int64: int}