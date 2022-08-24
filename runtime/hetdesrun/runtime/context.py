from pydantic import BaseModel


class ExecutionContext(BaseModel):
    currently_executed_transformation_id: str
    currently_executed_transformation_name: str
    currently_executed_transformation_type: str
    currently_executed_operator_hierarchical_id: str
    currently_executed_operator_hierarchical_name: str
