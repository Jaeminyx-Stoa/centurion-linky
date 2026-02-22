from pydantic import BaseModel


class ContraindicationWarning(BaseModel):
    severity: str  # "critical", "warning", "info"
    category: str  # "condition", "allergy", "medication"
    procedure_name: str
    detail: str
    matched_customer_item: str
    matched_procedure_item: str


class ContraindicationCheckResponse(BaseModel):
    has_warnings: bool
    critical_count: int
    warning_count: int
    info_count: int
    warnings: list[ContraindicationWarning]
