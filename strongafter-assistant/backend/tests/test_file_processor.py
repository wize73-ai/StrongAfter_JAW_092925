import os
import tempfile
import unittest
from models.excerpt import Excerpt
from utils.file_processor import (
    get_title_from_filename,
    extract_title_from_content,
    chunk_markdown_file,
    process_all_markdown_files
)


class TestFileProcessor(unittest.TestCase):
    
    def test_get_title_from_filename(self):
        # Test basic filename
        self.assertEqual(get_title_from_filename("test.md"), "test")
        
        # Test with underscores and hyphens
        self.assertEqual(get_title_from_filename("test_file-name.md"), "test file name")
        
        # Test with leading number
        self.assertEqual(get_title_from_filename("1. Introduction.md"), "Introduction")
        
        # Test with chapter format
        self.assertEqual(get_title_from_filename("Chapter 3 - Recovery.md"), "Recovery")
    
    def test_extract_title_from_content(self):
        # Test with H1 at the beginning
        content = "# My Document Title\n\nThis is some content."
        self.assertEqual(extract_title_from_content(content), "My Document Title")
        
        # Test with H1 after some content
        content = "Some metadata\n\n# My Document Title\n\nThis is some content."
        self.assertEqual(extract_title_from_content(content), "My Document Title")
        
        # Test with no H1
        content = "This is some content without a title."
        self.assertIsNone(extract_title_from_content(content))
        
        # Test with multiple H1s (should return the first one)
        content = "# First Title\n\nSome content\n\n# Second Title"
        self.assertEqual(extract_title_from_content(content), "First Title")
    
    def test_chunk_markdown_file(self):
        # Create a temporary markdown file for testing
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as temp:
            temp.write("# Test Document\n\n")
            temp.write("This is paragraph one.\nIt has two lines.\n\n")
            temp.write("This is paragraph two.\nIt also has two lines.\n\n")
            temp.write("This is paragraph three.\nIt has multiple lines.\nThree lines in fact.\n\n")
            temp.write("This is paragraph four.\nAnother multi-line paragraph.\nWith several sentences.\nFour lines total.\n\n")
            temp_path = temp.name
        
        try:
            # Test with default chunk size (6 lines)
            excerpts = chunk_markdown_file(temp_path)
            
            # Check that we got some excerpts
            self.assertGreater(len(excerpts), 0)
            
            # Check that all excerpts are of the right type
            for excerpt in excerpts:
                self.assertIsInstance(excerpt, Excerpt)
                self.assertEqual(excerpt.title, "Test Document")
                self.assertIn("https://strongafter.org/resources/test-document", excerpt.url)
            
            # Test with smaller chunk size
            small_excerpts = chunk_markdown_file(temp_path, chunk_size=3)
            self.assertGreater(len(small_excerpts), len(excerpts))
            
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)
    
    def test_process_all_markdown_files(self):
        # Create a temporary directory with markdown files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a few markdown files
            for i in range(3):
                with open(os.path.join(temp_dir, f"test{i}.md"), "w") as f:
                    f.write(f"# Test Document {i}\n\n")
                    f.write(f"This is file {i}, paragraph 1.\n\n")
                    f.write(f"This is file {i}, paragraph 2.\n\n")
            
            # Process all files
            excerpts = process_all_markdown_files(temp_dir)
            
            # Check we have excerpts from all files
            self.assertGreaterEqual(len(excerpts), 3)
            
            # Check titles are correct
            titles = set(excerpt.title for excerpt in excerpts)
            self.assertGreaterEqual(len(titles), 3)
            for i in range(3):
                self.assertIn(f"Test Document {i}", titles)


if __name__ == "__main__":
    unittest.main() 