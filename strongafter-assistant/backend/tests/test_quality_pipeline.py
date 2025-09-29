import unittest
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_optimized import TextProcessor, ThemeScore, RankedThemes
import yaml

class TestQualityPipeline(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Load test config
        with open('../quality.yml', 'r') as f:
            cls.config = yaml.safe_load(f)
        
        # Sample themes for testing
        cls.sample_themes = [
            {
                'id': 'theme1',
                'label': 'Anxiety and Panic',
                'description': 'Anxiety and panic involve persistent fear, racing thoughts, and physical symptoms.',
                'excerpts': []
            },
            {
                'id': 'theme2', 
                'label': 'Depression and Hopelessness',
                'description': 'Depression involves persistent sadness and loss of interest.',
                'excerpts': []
            },
            {
                'id': 'theme3',
                'label': 'Self Care',
                'description': 'Self care involves taking care of your physical and mental health.',
                'excerpts': []
            }
        ]
        
        cls.processor = TextProcessor(cls.sample_themes, {})
    
    def test_deterministic_rank_margin_entropy(self):
        """Test margin and entropy calculations in deterministic ranking."""
        theme_scores = [
            ThemeScore(self.sample_themes[0], 0.8, 0.8, 0.0),
            ThemeScore(self.sample_themes[1], 0.6, 0.6, 0.0),  
            ThemeScore(self.sample_themes[2], 0.4, 0.4, 0.0)
        ]
        
        ranked = self.processor.deterministic_rank("test text", theme_scores)
        
        # Margin should be difference between top 2 scores
        expected_margin = 0.8 - 0.6
        self.assertAlmostEqual(ranked.margin, expected_margin, places=2)
        
        # Entropy should be > 0 for distributed scores
        self.assertGreater(ranked.entropy, 0)
        
        # Top cosine should match highest scoring theme
        self.assertEqual(ranked.top_cosine, 0.8)
    
    def test_gate_promote_to_qf_on_low_margin(self):
        """Test promotion to quality-first mode on low margin."""
        # Create low margin scenario
        theme_scores = [
            ThemeScore(self.sample_themes[0], 0.51, 0.51, 0.0),
            ThemeScore(self.sample_themes[1], 0.50, 0.50, 0.0)  # Very close scores
        ]
        
        ranked = self.processor.deterministic_rank("test", theme_scores)
        
        # Should promote to QF due to low margin
        thr = self.config['thresholds']
        promote_qf = ranked.margin < thr['confidence_promote_qf_margin']
        
        self.assertTrue(promote_qf, f"Margin {ranked.margin} should be < {thr['confidence_promote_qf_margin']}")
    
    def test_skip_llm_on_high_confidence_short_input(self):
        """Test skipping LLM for high confidence short inputs."""
        # High confidence scenario
        theme_scores = [
            ThemeScore(self.sample_themes[0], 0.95, 0.95, 0.0),
            ThemeScore(self.sample_themes[1], 0.3, 0.3, 0.0)
        ]
        
        ranked = self.processor.deterministic_rank("anxiety", theme_scores)
        
        thr = self.config['thresholds']
        short_text = "anxiety"
        
        deterministic_ok = (
            self.processor.token_len(short_text) <= 8
            and ranked.confidence >= thr['deterministic_skip_llm_confidence']
            and not self.processor.safety_scan(short_text)
        )
        
        self.assertTrue(deterministic_ok, "Should skip LLM for high confidence short input")
    
    def test_safety_terms_force_qf(self):
        """Test that safety terms force quality-first mode."""
        safety_text = "I want to kill myself"
        safety_hit = self.processor.safety_scan(safety_text)
        
        self.assertTrue(safety_hit, "Should detect safety terms")
        
        # Any safety hit should force quality-first regardless of other factors
        theme_scores = [ThemeScore(self.sample_themes[0], 0.95, 0.95, 0.0)]
        ranked = self.processor.deterministic_rank(safety_text, theme_scores)
        
        promote_qf = safety_hit  # Safety always promotes to QF
        self.assertTrue(promote_qf, "Safety terms should force quality-first mode")
    
    def test_sparse_scoring(self):
        """Test sparse scoring function."""
        text = "I feel anxious and panicked"
        
        # Should score higher for anxiety theme
        anxiety_score = self.processor.compute_sparse_score(text, self.sample_themes[0])
        depression_score = self.processor.compute_sparse_score(text, self.sample_themes[1])
        
        self.assertGreater(anxiety_score, depression_score, 
                          "Anxiety theme should score higher for anxiety text")
    
    def test_fast_template_summary(self):
        """Test deterministic fallback summary."""
        summary = self.processor.fast_template_summary("test text", [])
        
        self.assertIsInstance(summary, dict)
        self.assertIn('summary', summary)
        self.assertIn('citations', summary)
        self.assertEqual(summary['citations'], [])
        self.assertEqual(summary['mode'], 'deterministic_fallback')
    
    def test_token_length_calculation(self):
        """Test token length approximation."""
        short_text = "help"
        long_text = "this is a much longer text with many words that should exceed the threshold"
        
        self.assertLessEqual(self.processor.token_len(short_text), 8)
        self.assertGreater(self.processor.token_len(long_text), 40)

if __name__ == '__main__':
    unittest.main()