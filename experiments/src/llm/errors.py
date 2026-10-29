class LLMError(Exception): pass
class LLMAuthError(LLMError): pass
class LLMBadRequestError(LLMError): pass

class LLMRateLimitError(LLMError):
    def __init__(self, message: str, retry_after_s: float | None = None):
        super().__init__(message)
        self.retry_after_s = retry_after_s

class LLMServerError(LLMError): pass
class LLMTimeoutError(LLMError): pass
