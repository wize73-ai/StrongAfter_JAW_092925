import unittest
import json
import os
import tempfile
from app import app


class TestAPI(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = self.app.get('/api/health')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('version', data)
    
    def test_excerpts_endpoint(self):
        """Test the excerpts endpoint."""
        # Create a temporary directory with a markdown file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test markdown file
            with open(os.path.join(temp_dir, "test.md"), "w") as f:
                f.write("# Test Document\n\n")
                f.write("This is a test paragraph.\n")
                f.write("It has multiple lines.\n\n")
                f.write("This is another paragraph.\n")
            
            # Set the app's RESOURCES_DIR to the temp directory
            app.config['RESOURCES_DIR'] = temp_dir
            
            # Get the excerpts
            response = self.app.get('/api/excerpts')
            
            # Check response
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertIn('excerpts', data)
            self.assertGreater(len(data['excerpts']), 0)
            
            # Check excerpt structure
            excerpt = data['excerpts'][0]
            self.assertIn('text', excerpt)
            self.assertIn('title', excerpt)
            self.assertIn('url', excerpt)
            self.assertEqual(excerpt['title'], 'Test Document')


if __name__ == '__main__':
    unittest.main() 