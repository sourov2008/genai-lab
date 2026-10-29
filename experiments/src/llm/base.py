
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class Message(BaseModel):
    role: str
    content: str

class LLMRequest(BaseModel):
    messages: list[Message]
    temperature: float = 0.0
    max_tokens: int = 2048

class LLMUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    cost_usd: float

class LLMResponse(BaseModel, Generic[T]):
    text: str
    parsed: T | None
    model: str
    provider: str
    usage: LLMUsage
    latency_ms: int
    request_id: str

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse: ...
    @abstractmethod
    async def complete_json(self, request: LLMRequest, schema: Type[T]) -> LLMResponse[T]: ...
