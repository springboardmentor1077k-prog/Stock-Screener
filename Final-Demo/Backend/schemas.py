from pydantic import BaseModel

class NLQueryRequest(BaseModel):
    query: str

class QueryHistoryResponse(BaseModel):
    nl_query: str
    dsl: dict
    created_at: str