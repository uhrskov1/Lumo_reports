from enum import Enum


class EnhancedEnum(Enum):
    def __str__(self) -> str:
        return f"{self.name}: {self.value}"

    @classmethod
    def get_groups(cls) -> dict:
        return dict(cls.__members__)

    @classmethod
    def print_groups(cls) -> None:
        print(f"Available Groups from the Data Source: {cls.__name__}:\n")
        for val in cls.get_groups().values():
            print(val)
