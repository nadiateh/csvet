from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator


class NormalizeText(BaseModel):
    type: Literal["normalize_text"]
    column: str
    case: Literal["title", "upper", "lower", "keep"] = "keep"
    reason: str


class MapValues(BaseModel):
    type: Literal["map_values"]
    column: str
    mapping: dict[str, str] = Field(min_length=1)
    reason: str


class ParseDates(BaseModel):
    type: Literal["parse_dates"]
    column: str
    input_formats: list[str] = Field(min_length=1)
    reason: str


class ToNumber(BaseModel):
    type: Literal["to_number"]
    column: str
    reason: str


class FlagRange(BaseModel):
    type: Literal["flag_range"]
    column: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    reason: str

    @model_validator(mode="after")
    def check_limits(self):
        if self.min_value is None and self.max_value is None:
            raise ValueError("give at least one of min_value or max_value")
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError("min_value must not be bigger than max_value")
        return self


Rule = Annotated[
    Union[NormalizeText, MapValues, ParseDates, ToNumber, FlagRange],
    Field(discriminator="type"),
]


class RuleSet(BaseModel):
    rules: list[Rule]