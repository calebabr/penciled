"""Base model for every generated contract (hand-written; generated.py builds on it).

Parse rules shared with the zod side (shared/ts):
- Unknown keys are DROPPED, never rejected (extra="ignore").
- Strict types: no string-to-int or int-to-bool coercion, matching zod.
- An optional, non-nullable property may be omitted but not sent as null
  (zod `.optional()` rejects null too); see `contract_non_null`.
- Canonical JSON (`to_json_dict`) leaves out absent optional properties, keeps
  explicit nulls, and always includes properties that have a schema default.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self

from pydantic import BaseModel, ConfigDict, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        strict=True,
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
    )

    # JSON names of optional properties that must not be null when present.
    contract_non_null: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="before")
    @classmethod
    def _reject_null_optionals(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in cls.contract_non_null:
                if key in data and data[key] is None:
                    raise ValueError(f"{key} may be omitted but must not be null")
        return data

    @model_validator(mode="after")
    def _mark_defaults_set(self) -> Self:
        # Defaults count as set so they always serialize (zod `.default()` does the same).
        for name, field in type(self).model_fields.items():
            if not field.is_required() and field.default is not None:
                self.__pydantic_fields_set__.add(name)
        return self

    def to_json_dict(self) -> dict[str, Any]:
        """Canonical JSON-compatible dict (aliases, absent optionals left out)."""
        return self.model_dump(mode="json", by_alias=True, exclude_unset=True)
