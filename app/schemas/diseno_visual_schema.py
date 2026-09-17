from pydantic import BaseModel
from typing import Optional, List

# Config schemas
class DisenoVisualConfigBase(BaseModel):
    fuente_principal: Optional[str] = None
    fuente_secundaria: Optional[str] = None
    estilo_iconos: Optional[str] = None
    libreria_iconos: Optional[str] = "Bootstrap Icons"
    grosor_iconos: Optional[float] = 1.5
    escala_espaciado_base: Optional[int] = 8
    radio_borde_base: Optional[int] = 8
    grid_columnas: Optional[int] = 12
    grid_gutter: Optional[int] = 16

class DisenoVisualConfigCreate(DisenoVisualConfigBase):
    proyecto_id: int

class DisenoVisualConfigResponse(DisenoVisualConfigBase):
    id: int
    proyecto_id: int
    class Config:
        from_attributes = True

# Color schemas
class ColorItemBase(BaseModel):
    hex_code: str
    nombre: str
    token_name: Optional[str] = None
    uso: str
    orden: Optional[int] = 0

class ColorItemCreate(ColorItemBase):
    proyecto_id: int

class ColorItemUpdate(ColorItemBase):
    pass

class ColorItemResponse(ColorItemBase):
    id: int
    proyecto_id: int
    class Config:
        from_attributes = True

# Typography schemas
class TypographyItemBase(BaseModel):
    estilo: str
    tamano_px: int
    peso: str
    interlineado: float
    tipo_fuente: Optional[str] = "Principal"
    orden: Optional[int] = 0

class TypographyItemCreate(TypographyItemBase):
    proyecto_id: int

class TypographyItemUpdate(TypographyItemBase):
    pass

class TypographyItemResponse(TypographyItemBase):
    id: int
    proyecto_id: int
    class Config:
        from_attributes = True

# Icon schemas
class IconItemBase(BaseModel):
    nombre: str
    token_name: str
    svg_content: str
    estilo: Optional[str] = None

class IconItemCreate(IconItemBase):
    proyecto_id: int

class IconItemUpdate(IconItemBase):
    pass

class IconItemResponse(IconItemBase):
    id: int
    proyecto_id: int
    class Config:
        from_attributes = True

# Combined Response
class DisenoVisualCompletoResponse(BaseModel):
    config: Optional[DisenoVisualConfigResponse]
    colores: List[ColorItemResponse]
    tipografias: List[TypographyItemResponse]
    iconos: List[IconItemResponse]
