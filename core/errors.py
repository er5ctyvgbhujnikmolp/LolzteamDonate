class BaseCoreException(Exception):
    ...

# LOLZ Api's
class BaseLolzApiException(BaseCoreException):
    ...

class TokenNotProvidedException(BaseLolzApiException, ValueError):
    ...

class BadApiRequestException(BaseLolzApiException):
    ...


# DontationAlert Api's
class BaseDAException(BaseCoreException):
    ...

class SendAlertException(BaseDAException):
    ...

# Payment Monitor
class BasePMException(BaseCoreException):
    ...

class InitializeException(BasePMException):
    ...

class TaskCanceled(BasePMException):
    ...