from enum import Enum, EnumMeta
from typing import TypeVar

_T = TypeVar("_T", bound=Enum)


class ComprehensiveSearchEnum(EnumMeta):
    def __contains__(cls: type[_T], obj: object) -> bool: # pyright: ignore[reportGeneralTypeIssues]
        if isinstance(obj, str):
            enum_item: _T | None = ComprehensiveSearchEnum._search_by_name(cls, str(obj))
            if enum_item:
                return True

        return isinstance(obj, cls) or obj in [d.value for d in cls]

    def __getitem__(cls: type[_T], name: str) -> _T: # pyright: ignore[reportGeneralTypeIssues]
        enum_item: _T | None = ComprehensiveSearchEnum._search_by_name(cls, name)
        if enum_item:
            return enum_item

        return super().__getitem__(name)
    
    def _search_by_name(cls: type[_T], name: str) -> _T | None: # pyright: ignore[reportGeneralTypeIssues]
        for direction in cls:
            if direction.name.lower() == name.lower():
                # check lowercase version of the name of each enum
                return direction
            elif direction.name[0].lower() == name[0].lower():
                # check the first letter (n, e, w, s)
                return direction
        
        return None