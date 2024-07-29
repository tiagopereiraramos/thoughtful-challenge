import dataclasses
from dataclasses import dataclass


@dataclass
class Payload:
    """
    A class to represent a payload for a specific operation.

    Attributes:
    -----------
    phrase_test : str
        A phrase to be tested (default is an empty string).
    section : str
        A section identifier (default is an empty string).
    sort_by : int
        A parameter to sort the results by (default is an empty integer).
    results : int
        The number of results to be returned (default is 0).

    Methods:
    --------
    to_dict():
        Converts the Payload instance to a dictionary.
    __str__():
        Returns a string representation containing only the non-default field values.
    """

    phrase_test: str = ""
    section: str = ""
    sort_by: int = ""
    results: int = 0

    def to_dict(self):
        """
        Converts the Payload instance to a dictionary.

        Returns:
        --------
        dict
            A dictionary containing all the attributes of the Payload instance.
        """
        return {
            "phrase_test": self.phrase_test,
            "section": self.section,
            "sort_by": self.sort_by,
            "results": self.results,
        }

    def __str__(self):
        """
        Returns a string containing only the non-default field values.

        Returns:
        --------
        str
            A string representation of the Payload instance with only the non-default values.
        """
        s = ", ".join(
            f"{field.name}={getattr(self, field.name)!r}"
            for field in dataclasses.fields(self)
            if getattr(self, field.name)
        )
        return f"{type(self).__name__}({s})"
