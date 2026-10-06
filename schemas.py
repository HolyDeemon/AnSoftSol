from pydantic import BaseModel, field_validator
from typing import List
from datetime import datetime
import ast

class SDocs(BaseModel):
    text: str
    created_date: datetime
    rubrics: list[str]

    @field_validator("rubrics", mode="before")
    @classmethod
    def parse_rubrics(cls, v):
        v = v.strip()
        if not v:
            return []
        try:
            parsed = ast.literal_eval(v)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except (ValueError, SyntaxError):
            return v
        return [r.strip().strip("'\"") for r in v.split(",") if r.strip()]
