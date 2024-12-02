from pydantic import BaseModel

def create_pydantic_class_from_yaml(schema):
    class_name, fields = list(schema.items())[0]
    annotations = {field: eval(type_hint) for field, type_hint in fields.items()}

    # Use 'type' to create the Pydantic class dynamically
    pydantic_class = type(
        class_name,
        (BaseModel,),  # Base classes (Pydantic BaseModel)
        {"__annotations__": annotations},  # Annotations for fields
    )

    return pydantic_class