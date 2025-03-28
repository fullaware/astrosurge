from pydantic import BaseModel, Field
from typing import List, Optional, Union
from bson import ObjectId, Int64
from datetime import datetime


class PyObjectId(ObjectId):
    """
    Custom ObjectId type for Pydantic validation.
    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class PyInt64(Int64):
    """
    Custom Int64 type for Pydantic validation.
    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, (int, Int64)):
            raise ValueError("Invalid Int64 value")
        return Int64(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="integer")


class UserModel(BaseModel):
    id: PyObjectId = Field(alias="_id")
    username: str
    password_hash: str
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, Int64: int}


class AsteroidElementModel(BaseModel):
    name: str
    mass_kg: PyInt64
    number: int


class AsteroidModel(BaseModel):
    id: PyObjectId = Field(alias="_id")
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

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, Int64: int}


class ElementClassModel(BaseModel):
    class_name: str = Field(alias="class")
    percentage: int


class ElementModel(BaseModel):
    id: PyObjectId = Field(alias="_id")
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
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    ship_id: PyObjectId
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
    id: PyObjectId = Field(alias="_id")
    name: str
    user_id: PyObjectId
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