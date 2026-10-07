"""通用响应/分页 Schema - 对应 PRD §11"""
from typing import Any, Generic, Optional, TypeVar, List
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """标准成功响应"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    code: int
    message: str
    detail: Optional[Any] = None
    request_id: Optional[str] = None


class PageMeta(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0


class PageResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: List[T] = []
    meta: PageMeta = PageMeta()


class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
