from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Excerpt:
    """
    Represents a chunk of text from a larger document.
    """
    text: str
    headers: List[str]
    book_url: str
    title: str
    embedding: Optional[List[float]] = None
    
    def to_dict(self):
        """
        Convert the excerpt to a dictionary for JSON serialization.
        """
        return {
            "text": self.text,
            "headers": self.headers,
            "book_url": self.book_url,
            "title": self.title,
            "embedding": self.embedding
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create an Excerpt from a dictionary.
        """
        return cls(
            text=data.get("text", ""),
            headers=data.get("headers", []),
            book_url=data.get("book_url", ""),
            title=data.get("title", ""),
            embedding=data.get("embedding")
        ) 