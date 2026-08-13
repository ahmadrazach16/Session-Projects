class BusinessRuleError(Exception):
    """Raised whenever a business rule rejects an operation."""
    def __init__(self, message, code="BUSINESS_RULE_VIOLATION", status_code=400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class NotFoundError(BusinessRuleError):
    def __init__(self, message):
        super().__init__(message, code="NOT_FOUND", status_code=404)


class UnauthorizedError(BusinessRuleError):
    def __init__(self, message="Unauthorized"):
        super().__init__(message, code="UNAUTHORIZED", status_code=401)


class ForbiddenError(BusinessRuleError):
    def __init__(self, message="Forbidden"):
        super().__init__(message, code="FORBIDDEN", status_code=403)
