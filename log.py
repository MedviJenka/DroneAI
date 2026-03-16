import logfire
from dataclasses import dataclass, field
from settings import Config


@dataclass
class Log:

    name: str
    _logger: dict = field(init=False, default=None)

    @property
    def fire(self) -> "Logfire":
        return logfire.configure(service_name=self.name, token=Config.LOGFIRE_TOKEN)
