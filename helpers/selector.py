import dataclasses
from dataclasses import dataclass, field


@dataclass
class Selector:
    """
    A class to represent a selector for web elements.

    Attributes:
    -----------
    css : str
        The CSS selector (default is an empty string).
    xpath : str
        The XPath selector (default is an empty string).
    text : str
        The text content to be matched (default is an empty string).
    attr : tuple
        A tuple containing additional attributes (default is an empty tuple).

    Methods:
    --------
    __str__():
        Returns a string representation containing only the non-default field values.
    """

    css: str = ""
    xpath: str = ""
    text: str = ""
    attr: tuple = field(default_factory=tuple)

    def __str__(self):
        """
        Returns a string containing only the non-default field values.

        Returns:
        --------
        str
            A string representation of the Selector instance with only the non-default values.
        """
        s = ", ".join(
            f"{field.name}={getattr(self, field.name)!r}"
            for field in dataclasses.fields(self)
            if getattr(self, field.name)
        )
        return f"{type(self).__name__}({s})"
