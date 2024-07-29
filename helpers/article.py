import dataclasses
import json
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Article:
    """
    A class to represent an article with various attributes.

    Attributes:
    -----------
    title : str
        The title of the article (default is an empty string).
    date : datetime
        The publication date of the article (default is an empty string).
    description : str
        A description of the article (default is an empty string).
    picture_filename : str
        The filename of the picture associated with the article (default is an empty string).
    picture_local_path : str
        The local path to the picture associated with the article (default is an empty string).
    title_count_phrase : int
        The count of a specific phrase in the title (default is 0).
    description_count_phrase : int
        The count of a specific phrase in the description (default is 0).
    find_money_title_description : bool
        A flag indicating if the term 'money' is found in the title or description (default is False).

    Methods:
    --------
    to_dict():
        Converts the Article instance to a dictionary.
    articles_to_json(articles):
        Converts a list of Article instances to a JSON string.
    __str__():
        Returns a string representation containing only the non-default field values.
    """

    title: str = ""
    date: datetime = ""
    description: str = ""
    picture_filename: str = ""
    picture_local_path: str = ""
    title_count_phrase: int = 0
    description_count_phrase: int = 0
    find_money_title_description: bool = False

    def to_dict(self):
        """
        Converts the Article instance to a dictionary.

        Returns:
        --------
        dict
            A dictionary containing all the attributes of the Article instance.
        """
        formatted_date = self.date.isoformat() if self.date else ""

        return {
            "title": self.title,
            "date": formatted_date,
            "description": self.description,
            "picture_filename": self.picture_filename,
            "picture_local_path": self.picture_local_path,
            "title_count_phrase": self.title_count_phrase,
            "description_count_phrase": self.description_count_phrase,
            "find_money_title_description": self.find_money_title_description,
        }

    @staticmethod
    def articles_to_json(articles):
        """
        Converts a list of Article instances to a JSON string.

        Parameters:
        -----------
        articles : list
            A list of Article instances.

        Returns:
        --------
        str
            A JSON string representation of the list of Article instances.
        """
        return json.dumps([article.to_dict() for article in articles], indent=4)

    def __str__(self):
        """
        Returns a string containing only the non-default field values.

        Returns:
        --------
        str
            A string representation of the Article instance with only the non-default values.
        """
        s = ", ".join(
            f"{field.name}={getattr(self, field.name)!r}"
            for field in dataclasses.fields(self)
            if getattr(self, field.name)
        )
        return f"{type(self).__name__}({s})"
