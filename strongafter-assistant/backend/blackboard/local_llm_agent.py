"""
Local LLM Agent for Fast Theme Analysis

This agent uses a locally hosted language model (Llama, Mistral, etc.)
for rapid theme ranking and analysis, significantly reducing API costs
and response times compared to cloud-based models.
"""

import asyncio
import logging
import json
import re
import time
from typing import Dict, Any, List, Optional
import requests
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentCapabilities
from .blackboard import TherapyBlackboard


logger = logging.getLogger(__name__)


@dataclass
class LocalLLMConfig:
    """Configuration for local LLM connection"""
    host: str = "localhost"
    port: int = 11434
    model_name: str = "llama3.1:8b"
    timeout: float = 30.0
    temperature: float = 0.1
    max_tokens: int = 2000


class LocalLLMAgent(BaseAgent):
    """
    Agent that uses a local LLM (via Ollama) for fast theme analysis.

    This agent handles:
    - Fast theme relevance scoring
    - Theme filtering and ranking
    - Confidence assessment
    - Fallback to cloud models if needed
    """

    def __init__(self, blackboard: TherapyBlackboard, config: Optional[LocalLLMConfig] = None):
        capabilities = AgentCapabilities(
            can_process_parallel=True,
            requires_gpu=True,
            estimated_processing_time=1.0,
            confidence_threshold=0.8,
            fallback_available=True
        )

        super().__init__(
            name="LocalLLMAgent",
            blackboard=blackboard,
            priority=10,  # High priority for fast processing
            capabilities=capabilities
        )

        self.config = config or LocalLLMConfig()
        self.base_url = f"http://{self.config.host}:{self.config.port}"
        self.is_available = False
        self.model_loaded = False

        # Initialize and check availability
        # Note: async initialization will happen on first use
        self._initialization_attempted = False

    async def _initialize(self) -> None:
        """Initialize the local LLM connection"""
        try:
            await self._check_ollama_status()
            await self._ensure_model_loaded()
            self.is_available = True
            logger.info(f"Local LLM agent initialized successfully with {self.config.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize local LLM: {e}")
            self.is_available = False

    async def _check_ollama_status(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama not accessible: {e}")
            return False

    async def _ensure_model_loaded(self) -> bool:
        """Ensure the specified model is loaded"""
        try:
            # Check if model exists
            response = requests.get(f"{self.base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]

                if self.config.model_name not in model_names:
                    logger.warning(f"Model {self.config.model_name} not found. Available: {model_names}")
                    return False

                # Test model with a simple prompt
                test_response = await self._call_ollama("Test prompt", max_tokens=10)
                self.model_loaded = test_response is not None
                return self.model_loaded

        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False

    async def _call_ollama(self, prompt: str, max_tokens: Optional[int] = None) -> Optional[str]:
        """
        Make an API call to Ollama

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text or None if failed
        """
        try:
            payload = {
                "model": self.config.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": max_tokens or self.config.max_tokens
                }
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.config.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return None

    def can_contribute(self) -> bool:
        """Check if agent can contribute to theme analysis"""
        # LocalLLM agent is now disabled in favor of Gemini-based ThemeAnalysisAgent
        # Only contribute if Gemini analysis fails (fallback mode)
        local_llm_failed = self.blackboard.read('local_llm_failed')
        gemini_failed = self.blackboard.read('gemini_failed')

        # Only contribute as fallback if Gemini has failed
        if not gemini_failed:
            return False

        has_preprocessed = self.blackboard.has_data('preprocessed_text')
        has_themes = self.blackboard.has_data('theme_candidates')

        # Check if theme_scores is empty (not just if it exists)
        theme_scores = self.blackboard.read('theme_scores')
        scores_exist = theme_scores and len(theme_scores) > 0

        return has_preprocessed and has_themes and not scores_exist

    def get_prerequisites(self) -> List[str]:
        """Prerequisites for theme analysis"""
        return ['preprocessed_text', 'theme_candidates']

    def get_outputs(self) -> List[str]:
        """Outputs produced by this agent"""
        return ['theme_scores', 'selected_themes', 'theme_analysis_confidence']

    async def contribute(self) -> Dict[str, Any]:
        """
        Perform fast theme analysis using local LLM

        Returns:
            Dictionary containing theme scores and analysis results
        """
        start_time = time.time()

        # Initialize if not already done
        if not self._initialization_attempted:
            await self._initialize()
            self._initialization_attempted = True

        # Get input data
        user_text = self.blackboard.read('preprocessed_text')
        theme_candidates = self.blackboard.read('theme_candidates')

        if not user_text or not theme_candidates:
            raise ValueError("Missing required input data for theme analysis")

        logger.info(f"Starting local LLM theme analysis for {len(theme_candidates)} themes")

        try:
            # Generate theme scores
            theme_scores = await self._analyze_themes(user_text, theme_candidates)

            # Select top themes
            selected_themes = self._select_top_themes(theme_scores, theme_candidates)

            # Calculate confidence
            confidence = self._calculate_confidence(theme_scores)

            # Write results to blackboard
            self.blackboard.write('theme_scores', theme_scores, self.name, confidence)
            self.blackboard.write('selected_themes', selected_themes, self.name, confidence)
            self.blackboard.write('theme_analysis_confidence', confidence, self.name)

            # Add streaming update
            self.blackboard.add_streaming_update({
                'type': 'theme_analysis_complete',
                'selected_themes': len(selected_themes),
                'confidence': confidence,
                'processing_time': time.time() - start_time
            }, self.name)

            processing_time = time.time() - start_time
            logger.info(f"Local LLM theme analysis completed in {processing_time:.2f}s")

            return {
                'success': True,
                'theme_scores': theme_scores,
                'selected_themes': selected_themes,
                'confidence': confidence,
                'processing_time': processing_time,
                'outputs': ['theme_scores', 'selected_themes', 'theme_analysis_confidence']
            }

        except Exception as e:
            logger.error(f"Local LLM theme analysis failed: {e}")
            # Trigger fallback
            self.blackboard.write('local_llm_failed', True, self.name)
            raise

    async def _analyze_themes(self, user_text: str, themes: List[Dict]) -> Dict[str, float]:
        """
        Analyze theme relevance using local LLM

        Args:
            user_text: User's input text
            themes: List of theme dictionaries

        Returns:
            Dictionary mapping theme IDs to relevance scores
        """
        # Build optimized prompt for local model
        prompt = self._build_analysis_prompt(user_text, themes)

        # Get response from local LLM
        response = await self._call_ollama(prompt)

        if not response:
            raise RuntimeError("Local LLM did not return a response")

        # Debug logging for LLM response
        logger.info(f"LocalLLM raw response (first 500 chars): {response[:500]}")

        # Parse scores from response
        scores = self._parse_theme_scores(response, themes)

        # Debug logging for parsed scores
        logger.info(f"LocalLLM parsed scores sample: {dict(list(scores.items())[:5])}")

        return scores

    def _build_analysis_prompt(self, user_text: str, themes: List[Dict]) -> str:
        """
        Build an optimized prompt for fast theme analysis

        Args:
            user_text: User's input text
            themes: List of themes to analyze

        Returns:
            Formatted prompt string
        """
        # Debug logging
        logger.info(f"LocalLLM building prompt with user_text: '{user_text}'")
        logger.info(f"LocalLLM analyzing {len(themes)} themes")

        # Create concise theme list
        theme_list = []
        for i, theme in enumerate(themes, 1):
            theme_list.append(f"{i}. {theme['label']}: {theme['description'][:100]}...")

        themes_text = "\n".join(theme_list)

        prompt = f"""You are analyzing theme relevance. Rate how relevant each theme is to the user's text on a scale of 0-100.

User input: "{user_text}"

Themes to rate:
{themes_text}

Instructions:
- Give a score from 0-100 for EACH theme
- 90-100: Directly addresses the theme
- 70-89: Strongly related
- 50-69: Moderately related
- 30-49: Weakly related
- 0-29: Not related

IMPORTANT: You must respond with ONLY a valid JSON object containing ALL theme scores. No other text.

Example format: {{"1": 85, "2": 20, "3": 5, "4": 60}}

Your response:"""

        logger.info(f"LocalLLM prompt length: {len(prompt)} characters")
        logger.info(f"LocalLLM prompt preview: {prompt[:200]}...")
        return prompt

    def _parse_theme_scores(self, response: str, themes: List[Dict]) -> Dict[str, float]:
        """
        Parse theme scores from LLM response

        Args:
            response: Raw LLM response
            themes: Original theme list

        Returns:
            Dictionary mapping theme IDs to scores
        """
        scores = {}

        try:
            # Try to extract complete JSON from response
            # Look for opening brace and find matching closing brace
            start_idx = response.find('{')
            if start_idx != -1:
                # Find the matching closing brace
                brace_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(response)):
                    if response[i] == '{':
                        brace_count += 1
                    elif response[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i
                            break

                if brace_count == 0:  # Found complete JSON
                    json_str = response[start_idx:end_idx + 1]
                    logger.info(f"LocalLLM extracted JSON: {json_str[:200]}...")
                    parsed_scores = json.loads(json_str)
                else:
                    raise ValueError("Incomplete JSON in response")

                # Map numeric keys to theme IDs
                for i, theme in enumerate(themes, 1):
                    key = str(i)
                    if key in parsed_scores:
                        score = float(parsed_scores[key])
                        scores[theme['id']] = max(0.0, min(100.0, score))  # Clamp 0-100

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse JSON scores, using fallback parsing: {e}")
            # Fallback: extract numbers from response
            numbers = re.findall(r'\d+', response)
            for i, theme in enumerate(themes):
                if i < len(numbers):
                    try:
                        score = float(numbers[i])
                        scores[theme['id']] = max(0.0, min(100.0, score))
                    except ValueError:
                        scores[theme['id']] = 0.0
                else:
                    scores[theme['id']] = 0.0

        # Ensure all themes have scores
        for theme in themes:
            if theme['id'] not in scores:
                scores[theme['id']] = 0.0

        return scores

    def _select_top_themes(self, scores: Dict[str, float], themes: List[Dict], max_themes: int = 3) -> List[Dict]:
        """
        Select top themes based on scores

        Args:
            scores: Theme relevance scores
            themes: Original theme list
            max_themes: Maximum number of themes to select

        Returns:
            List of selected theme dictionaries with scores
        """
        # Sort themes by score
        sorted_themes = sorted(
            themes,
            key=lambda theme: scores.get(theme['id'], 0.0),
            reverse=True
        )

        # Select top themes with minimum score threshold
        selected = []
        for theme in sorted_themes:
            theme_score = scores.get(theme['id'], 0.0)
            if theme_score >= 30.0 and len(selected) < max_themes:  # Minimum relevance threshold
                theme_with_score = theme.copy()
                theme_with_score['relevance_score'] = theme_score
                selected.append(theme_with_score)

        # Ensure at least one theme is selected
        if not selected and sorted_themes:
            top_theme = sorted_themes[0].copy()
            top_theme['relevance_score'] = scores.get(top_theme['id'], 0.0)
            selected.append(top_theme)

        logger.info(f"Selected {len(selected)} themes with scores: {[t['relevance_score'] for t in selected]}")
        return selected

    def _calculate_confidence(self, scores: Dict[str, float]) -> float:
        """
        Calculate confidence in the analysis based on score distribution

        Args:
            scores: Theme relevance scores

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not scores:
            return 0.0

        score_values = list(scores.values())
        max_score = max(score_values)
        mean_score = sum(score_values) / len(score_values)

        # High confidence if there's a clear winner with good separation
        if max_score >= 70.0 and (max_score - mean_score) >= 20.0:
            confidence = 0.9
        elif max_score >= 50.0 and (max_score - mean_score) >= 15.0:
            confidence = 0.8
        elif max_score >= 30.0:
            confidence = 0.7
        else:
            confidence = 0.6

        return confidence

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on local LLM

        Returns:
            Health status dictionary
        """
        try:
            start_time = time.time()
            test_response = await self._call_ollama("Hello", max_tokens=5)
            response_time = time.time() - start_time

            return {
                'available': test_response is not None,
                'model_loaded': self.model_loaded,
                'response_time': response_time,
                'model_name': self.config.model_name,
                'host': f"{self.config.host}:{self.config.port}"
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e),
                'model_name': self.config.model_name
            }