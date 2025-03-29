from pydantic import BaseModel, Field, ConfigDict, field_serializer, validator
from typing import List, Optional
from bson import ObjectId
from bson.int64 import Int64
from datetime import datetime


class UserModel(BaseModel):
    id: str = Field(alias="_id")
    username: str
    password_hash: str
    created_at: datetime
    last_login: Optional[datetime]

    # Convert the ObjectId from Mongo to a string
    @validator("id", pre=True)
    def convert_object_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

    class Config:
        arbitrary_types_allowed = True
        # Let Pydantic know how to handle ObjectId -> str in any JSON response
        json_encoders = {ObjectId: str}


class AsteroidElementModel(BaseModel):
    name: str
    mass_kg: Int64
    number: int


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
    mass: Int64
    value: Int64
    elements: List[AsteroidElementModel]

    @field_serializer("id")
    def serialize_objectid(self, value: ObjectId) -> str:
        return str(value)

    @field_serializer("mass", "value")
    def serialize_int64(self, value: Int64) -> int:
        return int(value)

    model_config = ConfigDict(arbitrary_types_allowed=True, json_encoders={ObjectId: str, Int64: int})


class ElementClassModel(BaseModel):
    class_name: str = Field(alias="class")
    percentage: int


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
    classes: List[ElementClassModel]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, Int64: int}


class MissionModel(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    ship_id: str
    asteroid_name: str
    success: bool
    distance: int
    estimated_value: PyInt64
    investment: int
    total_cost: int
    status: int
    created_at: datetime
    actual_duration: int
    planned_duration: int
    mined_elements: List[str]

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

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, Int64: int}