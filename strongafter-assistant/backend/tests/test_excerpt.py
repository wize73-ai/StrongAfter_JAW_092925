import unittest
from models.excerpt import Excerpt


class TestExcerpt(unittest.TestCase):
    
    def test_excerpt_creation(self):
        # Test creating an excerpt
        excerpt = Excerpt("Test text", "Test Title", "http://example.com")
        
        self.assertEqual(excerpt.text, "Test text")
        self.assertEqual(excerpt.title, "Test Title")
        self.assertEqual(excerpt.url, "http://example.com")
    
    def test_to_dict(self):
        # Test converting excerpt to dict
        excerpt = Excerpt("Test text", "Test Title", "http://example.com")
        excerpt_dict = excerpt.to_dict()
        
        self.assertIsInstance(excerpt_dict, dict)
        self.assertEqual(excerpt_dict["text"], "Test text")
        self.assertEqual(excerpt_dict["title"], "Test Title")
        self.assertEqual(excerpt_dict["url"], "http://example.com")
    
    def test_from_dict(self):
        # Test creating excerpt from dict
        data = {
            "text": "Test text",
            "title": "Test Title",
            "url": "http://example.com"
        }
        
        excerpt = Excerpt.from_dict(data)
        
        self.assertIsInstance(excerpt, Excerpt)
        self.assertEqual(excerpt.text, "Test text")
        self.assertEqual(excerpt.title, "Test Title")
        self.assertEqual(excerpt.url, "http://example.com")
    
    def test_from_dict_missing_fields(self):
        # Test with missing fields (should use defaults)
        data = {"title": "Only Title"}
        
        excerpt = Excerpt.from_dict(data)
        
        self.assertEqual(excerpt.text, "")
        self.assertEqual(excerpt.title, "Only Title")
        self.assertEqual(excerpt.url, "")


if __name__ == "__main__":
    unittest.main() 