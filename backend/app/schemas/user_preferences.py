from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


DietaryPreference = Literal[
    "vegetarian",
    "vegan",
    "pescatarian",
    "halal",
    "kosher",
]

Allergy = Literal[
    "peanuts",
    "tree_nuts",
    "milk",
    "eggs",
    "soy",
    "wheat",
    "fish",
    "shellfish",
    "sesame",
]

KitchenEquipment = Literal[
    "oven",
    "microwave",
    "air_fryer",
    "stovetop",
    "kettle",
    "toaster",
    "blender",
    "food_processor",
    "rice_cooker",
]


class UserPreferencesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dietary_preferences: list[DietaryPreference] = Field(default_factory=list, max_length=5)
    allergies: list[Allergy] = Field(default_factory=list, max_length=9)
    kitchen_equipment: list[KitchenEquipment] = Field(default_factory=list, max_length=9)

    @model_validator(mode="after")
    def validate_unique_values(self):
        if len(self.dietary_preferences) != len(set(self.dietary_preferences)):
            raise ValueError("Duplicate dietary preferences are not allowed.")

        if len(self.allergies) != len(set(self.allergies)):
            raise ValueError("Duplicate allergies are not allowed.")

        if len(self.kitchen_equipment) != len(set(self.kitchen_equipment)):
            raise ValueError("Duplicate kitchen equipment is not allowed.")

        return self


class UserPreferencesResponse(BaseModel):
    dietary_preferences: list[DietaryPreference]
    allergies: list[Allergy]
    kitchen_equipment: list[KitchenEquipment]