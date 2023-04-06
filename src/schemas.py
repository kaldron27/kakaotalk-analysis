from pydantic import BaseModel
from typing import Any
from bson import ObjectId


class DefaultReponse(BaseModel):
    error_code: int
    result: Any
    added_message: Any

    class Config:
        json_encoders = {ObjectId: str}

    @classmethod
    def success(cls, result: Any = None, added_message: Any = None):
        return cls.manual_code(result=result, added_message=added_message)

    @classmethod
    def fail(cls, error_code: int, result: Any, added_message: Any = None):
        """
        http status 200으로, error_code를 붙이고 싶을 때 사용
        """
        return cls.manual_code(error_code=error_code, result=result, added_message=added_message)

    @classmethod
    def manual_code(cls, error_code: int = 0, result: BaseModel = None, added_message: Any = None):
        return DefaultReponse.construct(error_code=error_code, result=result)


class DefaultModel(BaseModel):
    def __str__(self) -> str:
        return str(self.__dict__)
