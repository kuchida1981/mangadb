from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.appcontext import AppContext


class UsecaseProtocol(Protocol):
    def __init__(self, app: "AppContext"): ...
    def invoke(self): ...
