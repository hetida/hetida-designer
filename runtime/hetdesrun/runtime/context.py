from pydantic import BaseModel


class ExecutionContext(BaseModel):
    transformation_id: str
    transformation_name: str
    transformation_type: str
    operator_hierarchical_id: str
    operator_hierarchical_name: str
