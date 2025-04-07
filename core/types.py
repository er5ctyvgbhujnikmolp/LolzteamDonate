from dataclasses import dataclass


@dataclass
class AlertInfo():
    amount: float
    username: str
    message: str