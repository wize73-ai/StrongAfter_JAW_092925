"""
StrongAfter Knowledge Source Agents - Specialized Processing Units
=================================================================

Multi-agent system components for trauma recovery assistance processing.
Each agent specializes in specific therapeutic content analysis tasks.

Author: JAWilson
Created: September 2025
License: Proprietary - StrongAfter Systems

Agents included:
- ThemeAnalysisAgent: Semantic theme relevance scoring
- ExcerptRetrievalAgent: Content similarity and extraction
- SummaryGenerationAgent: Therapeutic response synthesis
- QualityAssuranceAgent: Response validation and safety checks
- StreamingAgent: Real-time progress updates
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List, Optional
import google.generativeai as genai

from .base_agent import BaseAgent, AgentCapabilities
from .blackboard import TherapyBlackboard


logger = logging.getLogger(__name__)


class ThemeAnalysisAgent(BaseAgent):
    """
    Primary agent responsible for analyzing themes using Gemini.
    Provides high-quality semantic understanding for theme relevance scoring.
    """

    def __init__(self, blackboard: TherapyBlackboard, gemini_model):
        capabilities = AgentCapabilities(
            can_process_parallel=True,  # Can run in parallel with other agents
            requires_gpu=False,
            estimated_processing_time=3.0,
            confidence_threshold=0.9,
            fallback_available=False
        )

        super().__init__(
            name="ThemeAnalysisAgent",
            blackboard=blackboard,
            priority=10,  # High priority for primary theme analysis
            capabilities=capabilities
        )

        self.gemini_model = gemini_model

    def can_contribute(self) -> bool:
        """Primary theme analysis agent - always ready when prerequisites are met"""
        has_preprocessed = self.blackboard.has_data('preprocessed_text')
        has_themes = self.blackboard.has_data('theme_candidates')

        # Check if theme_scores already exists (avoid duplicate work)
        theme_scores = self.blackboard.read('theme_scores')
        scores_exist = theme_scores and len(theme_scores) > 0

        return has_preprocessed and has_themes and not scores_exist

    def get_prerequisites(self) -> List[str]:
        return ['preprocessed_text', 'theme_candidates']

    def get_outputs(self) -> List[str]:
        return ['theme_scores', 'selected_themes', 'theme_analysis_confidence']

    async def contribute(self) -> Dict[str, Any]:
        """Primary theme analysis using Gemini for accurate semantic understanding"""
        start_time = time.time()

        user_text = self.blackboard.read('preprocessed_text')
        theme_candidates = self.blackboard.read('theme_candidates')

        logger.info(f"Starting primary Gemini theme analysis for {len(theme_candidates)} themes")

        try:
            # Use simplified Gemini analysis for speed
            scores = await self._analyze_themes_gemini(user_text, theme_candidates)
            selected_themes = self._select_top_themes(scores, theme_candidates)

            # Write results
            self.blackboard.write('theme_scores', scores, self.name, 0.9)
            self.blackboard.write('selected_themes', selected_themes, self.name, 0.9)
            self.blackboard.write('theme_analysis_confidence', 0.9, self.name)

            processing_time = time.time() - start_time
            logger.info(f"Gemini theme analysis completed in {processing_time:.2f}s")

            return {
                'success': True,
                'processing_time': processing_time,
                'confidence': 0.9,
                'outputs': self.get_outputs()
            }

        except Exception as e:
            logger.error(f"Gemini theme analysis failed: {e}")
            raise

    async def _analyze_themes_gemini(self, user_text: str, themes: List[Dict]) -> Dict[str, float]:
        """Primary Gemini theme analysis with enhanced semantic understanding"""
        # Create detailed theme list with descriptions
        theme_list = []
        for i, theme in enumerate(themes, 1):
            theme_list.append(f"{i}. {theme['label']}: {theme['description'][:150]}...")

        themes_text = "\n".join(theme_list)

        prompt = f"""You are analyzing the relevance of trauma recovery themes to a user's input. Be extremely strict about relevance.

User input: "{user_text}"

Themes to rate (0-100 scale):
{themes_text}

STRICT SCORING GUIDELINES:
- 90-100: User explicitly mentions trauma, abuse, recovery, therapy, or directly asks for help with trauma-related issues
- 70-89: User describes clear trauma symptoms (anxiety, depression, PTSD, addiction, relationship problems) in context
- 50-69: User mentions emotional struggles or mental health challenges that could relate to trauma
- 30-49: Very weak connection requiring significant inference
- 0-29: NO CONNECTION - user discusses unrelated topics

EXAMPLES OF LOW SCORES (0-29):
- Food preferences ("I love pizza", "favorite ice cream")
- Hobbies ("playing video games", "reading books", "hiking")
- Sports, weather, entertainment, shopping, travel
- General positive statements without distress context
- Casual daily activities

BE EXTREMELY STRICT: Only give scores above 30 if there's a clear emotional distress, mental health concern, or explicit trauma reference.

Return ONLY a valid JSON object with ALL theme scores:
{{"1": score, "2": score, "3": score, ...}}"""

        response = self.gemini_model.generate_content(prompt)

        logger.info(f"Gemini raw response (first 200 chars): {response.text[:200]}")

        # Parse response with improved error handling
        scores = {}
        try:
            # Try to extract JSON from response
            response_text = response.text.strip()

            # Find JSON object in response
            start_idx = response_text.find('{')
            if start_idx != -1:
                # Find matching closing brace
                brace_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(response_text)):
                    if response_text[i] == '{':
                        brace_count += 1
                    elif response_text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i
                            break

                if brace_count == 0:
                    json_str = response_text[start_idx:end_idx + 1]
                    logger.info(f"Gemini extracted JSON: {json_str[:200]}...")
                    parsed = json.loads(json_str)

                    for i, theme in enumerate(themes, 1):
                        key = str(i)
                        if key in parsed:
                            score = float(parsed[key])
                            scores[theme['id']] = max(0.0, min(100.0, score))  # Clamp 0-100
                        else:
                            scores[theme['id']] = 0.0
                else:
                    raise ValueError("Incomplete JSON in Gemini response")
            else:
                raise ValueError("No JSON found in Gemini response")

        except Exception as e:
            logger.warning(f"Failed to parse Gemini JSON response: {e}")
            # Fallback: give low relevance to prevent false positives
            for theme in themes:
                scores[theme['id']] = 10.0  # Low default relevance

        # Ensure all themes have scores
        for theme in themes:
            if theme['id'] not in scores:
                scores[theme['id']] = 0.0

        logger.info(f"Gemini parsed scores sample: {dict(list(scores.items())[:5])}")
        return scores

    def _select_top_themes(self, scores: Dict[str, float], themes: List[Dict], max_themes: int = 3) -> List[Dict]:
        """Select top themes based on relevance scores with minimum threshold"""
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
            if theme_score >= 20.0 and len(selected) < max_themes:  # Minimum relevance threshold
                theme_with_score = theme.copy()
                theme_with_score['relevance_score'] = theme_score
                selected.append(theme_with_score)

        # Only select a theme if it has a meaningful score (> 10)
        if not selected and sorted_themes:
            top_theme_score = scores.get(sorted_themes[0]['id'], 0.0)
            if top_theme_score > 10.0:  # Only select if there's some relevance
                top_theme = sorted_themes[0].copy()
                top_theme['relevance_score'] = top_theme_score
                selected.append(top_theme)

        logger.info(f"Gemini selected {len(selected)} themes with scores: {[t['relevance_score'] for t in selected]}")
        return selected


class ExcerptRetrievalAgent(BaseAgent):
    """
    Agent responsible for retrieving relevant excerpts using FAISS similarity search.
    """

    def __init__(self, blackboard: TherapyBlackboard, faiss_index=None):
        capabilities = AgentCapabilities(
            can_process_parallel=True,
            requires_gpu=False,
            estimated_processing_time=0.5,
            confidence_threshold=0.9,
            fallback_available=True
        )

        super().__init__(
            name="ExcerptRetrievalAgent",
            blackboard=blackboard,
            priority=7,
            capabilities=capabilities
        )

        self.faiss_index = faiss_index

    def can_contribute(self) -> bool:
        """Can contribute when themes are selected"""
        return (self.blackboard.has_data('selected_themes') and
                not self.blackboard.has_data('retrieved_excerpts'))

    def get_prerequisites(self) -> List[str]:
        return ['selected_themes']

    def get_outputs(self) -> List[str]:
        return ['retrieved_excerpts']

    async def contribute(self) -> Dict[str, Any]:
        """Retrieve excerpts for selected themes"""
        start_time = time.time()

        selected_themes = self.blackboard.read('selected_themes')
        logger.info(f"Retrieving excerpts for {len(selected_themes)} themes")

        try:
            excerpts = {}
            for theme in selected_themes:
                theme_excerpts = await self._get_excerpts_for_theme(theme)
                excerpts[theme['id']] = theme_excerpts

            self.blackboard.write('retrieved_excerpts', excerpts, self.name, 0.95)

            # Add streaming update
            self.blackboard.add_streaming_update({
                'type': 'excerpts_retrieved',
                'theme_count': len(excerpts),
                'total_excerpts': sum(len(ex) for ex in excerpts.values())
            }, self.name)

            processing_time = time.time() - start_time
            logger.info(f"Excerpt retrieval completed in {processing_time:.2f}s")

            return {
                'success': True,
                'processing_time': processing_time,
                'confidence': 0.95,
                'outputs': ['retrieved_excerpts']
            }

        except Exception as e:
            logger.error(f"Excerpt retrieval failed: {e}")
            raise

    async def _get_excerpts_for_theme(self, theme: Dict) -> List[Dict]:
        """Get excerpts for a specific theme"""
        # Use existing excerpt data from theme
        if 'excerpts' in theme:
            return theme['excerpts'][:5]  # Limit to top 5
        return []


class SummaryGenerationAgent(BaseAgent):
    """
    Agent responsible for generating high-quality summaries using Gemini.
    """

    def __init__(self, blackboard: TherapyBlackboard, gemini_model, book_metadata=None):
        capabilities = AgentCapabilities(
            can_process_parallel=False,  # Needs full context
            requires_gpu=False,
            estimated_processing_time=5.0,
            confidence_threshold=0.8,
            fallback_available=True
        )

        super().__init__(
            name="SummaryGenerationAgent",
            blackboard=blackboard,
            priority=6,
            capabilities=capabilities
        )

        self.gemini_model = gemini_model
        self.book_metadata = book_metadata or {}

    def can_contribute(self) -> bool:
        """Can contribute when themes are available"""
        return (self.blackboard.has_data('selected_themes') and
                not self.blackboard.has_data('final_response'))

    def get_prerequisites(self) -> List[str]:
        return ['selected_themes']

    def get_outputs(self) -> List[str]:
        return ['final_response', 'citations']

    async def contribute(self) -> Dict[str, Any]:
        """Generate comprehensive summary with citations"""
        start_time = time.time()

        themes = self.blackboard.read('selected_themes')
        user_text = self.blackboard.read('user_input')

        # If no themes were selected, generate a contextual response
        if not themes or len(themes) == 0:
            logger.info("No relevant trauma themes found - generating contextual response")

            # Generate a response that acknowledges the user's input
            prompt = f"""The user has shared: "{user_text}"

This input doesn't relate to trauma recovery or mental health topics.
Please provide a brief, friendly response that:
1. Acknowledges what they shared
2. Gently indicates this platform specializes in trauma recovery support
3. Offers to help if they have trauma-related concerns

Keep the response natural and conversational, not formulaic."""

            try:
                response_text = self.gemini_model.generate_content(prompt).text.strip()
            except:
                # Fallback if generation fails
                response_text = f"Thank you for sharing about {user_text[:50]}. While this platform specializes in trauma recovery and mental health support, I'm here if you need help with those topics."

            response = {
                'themes': [],
                'summary': response_text,
                'citations': [],
                'processing_time': time.time() - start_time
            }

            self.blackboard.write('final_response', response, self.name, 1.0)
            self.blackboard.write('citations', [], self.name)

            return {
                'success': True,
                'processing_time': time.time() - start_time,
                'confidence': 1.0,
                'outputs': ['final_response', 'citations']
            }

        # Try to get excerpts from ExcerptRetrievalAgent first, fallback to themes
        retrieved_excerpts = self.blackboard.read('retrieved_excerpts')
        if retrieved_excerpts:
            # Flatten the excerpts from the dictionary structure
            excerpts = []
            for theme_id, theme_excerpts in retrieved_excerpts.items():
                excerpts.extend(theme_excerpts)
        else:
            # Fallback: extract excerpts directly from themes
            excerpts = self._extract_excerpts_from_themes(themes)

        logger.info(f"Generating summary for {len(themes)} themes")

        try:
            summary = await self._generate_summary(user_text, themes, excerpts)
            citations = self._extract_citations(summary)

            response = {
                'themes': themes,
                'summary': summary,
                'citations': citations,
                'processing_time': time.time() - start_time
            }

            self.blackboard.write('final_response', response, self.name, 0.9)
            self.blackboard.write('citations', citations, self.name)

            # Add streaming update
            self.blackboard.add_streaming_update({
                'type': 'summary_complete',
                'summary_length': len(summary),
                'citation_count': len(citations)
            }, self.name)

            processing_time = time.time() - start_time
            logger.info(f"Summary generation completed in {processing_time:.2f}s")

            return {
                'success': True,
                'processing_time': processing_time,
                'confidence': 0.9,
                'outputs': ['final_response', 'citations']
            }

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            raise

    async def _generate_summary(self, user_text: str, themes: List[Dict], excerpts: List[Dict]) -> str:
        """Generate summary using existing logic"""
        # Build optimized prompt with excerpts list
        prompt = self._build_summary_prompt(user_text, themes, excerpts)

        response = self.gemini_model.generate_content(prompt)
        return response.text.strip()

    def _build_summary_prompt(self, user_text: str, themes: List[Dict], excerpts: List[Dict]) -> str:
        """Build optimized summary prompt"""
        themes_text = "\n".join([f"- {t['label']}: {t['description']}" for t in themes])

        excerpts_text = ""
        for i, item in enumerate(excerpts[:10], 1):  # Limit to top 10 for speed
            excerpt = item['excerpt']
            title = excerpt.get('title', 'Unknown')
            excerpts_text += f"EXCERPT {i} ({title}):\n{excerpt['text'][:500]}...\n\n"

        prompt = f"""Create a 2-paragraph therapeutic summary for trauma recovery using the provided themes and excerpts.

THEMES:
{themes_text}

EXCERPTS:
{excerpts_text}

INSTRUCTIONS:
- Write exactly 2 paragraphs about trauma recovery
- Reference specific excerpts throughout your summary
- Use citation format ¹ ² ³ etc. when referencing excerpts
- Include at least 3-5 citations from the excerpts above
- Make the summary supportive and therapeutic in tone
- Focus on healing, recovery, and practical insights

IMPORTANT: You MUST include citations in the format ¹ when referencing excerpt content.

After your summary, add a References section using this format:
## References
¹ Author, A. (Year). *Title*. Publisher. [Get this book](http://strongafter.org)
² Author, B. (Year). *Title*. Publisher. [Get this book](http://strongafter.org)"""

        return prompt

    def _extract_excerpts_from_themes(self, themes: List[Dict]) -> List[Dict]:
        """Extract all excerpts from themes for summary generation"""
        all_excerpts = []
        for theme in themes:
            if 'excerpts' in theme and theme['excerpts']:
                all_excerpts.extend(theme['excerpts'])
        return all_excerpts

    def _extract_citations(self, summary: str) -> List[Dict]:
        """Extract citation information from summary"""
        # Simple citation extraction
        import re
        # Look for both old format and new superscript format
        citations_old = re.findall(r'⁽(\d+)⁾', summary)
        citations_new = re.findall(r'([¹²³⁴⁵⁶⁷⁸⁹⁰]+)', summary)
        # Convert superscript to numbers
        superscript_map = {'⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'}
        citations_converted = []
        for c in citations_new:
            converted = ''.join(superscript_map.get(char, char) for char in c)
            citations_converted.append(converted)

        all_citations = citations_old + citations_converted
        return [{'number': int(c), 'type': 'excerpt'} for c in all_citations if c.isdigit()]


class QualityAssuranceAgent(BaseAgent):
    """
    Agent responsible for quality assurance and response validation.
    """

    def __init__(self, blackboard: TherapyBlackboard):
        capabilities = AgentCapabilities(
            can_process_parallel=True,
            requires_gpu=False,
            estimated_processing_time=0.2,
            confidence_threshold=0.7,
            fallback_available=False
        )

        super().__init__(
            name="QualityAssuranceAgent",
            blackboard=blackboard,
            priority=4,
            capabilities=capabilities
        )

    def can_contribute(self) -> bool:
        """Can contribute when final response is available"""
        return (self.blackboard.has_data('final_response') and
                not self.blackboard.has_data('quality_score'))

    def get_prerequisites(self) -> List[str]:
        return ['final_response']

    def get_outputs(self) -> List[str]:
        return ['quality_score', 'quality_report']

    async def contribute(self) -> Dict[str, Any]:
        """Assess response quality"""
        start_time = time.time()

        response = self.blackboard.read('final_response')
        logger.info("Performing quality assurance")

        try:
            quality_score = self._assess_quality(response)
            quality_report = self._generate_quality_report(response, quality_score)

            self.blackboard.write('quality_score', quality_score, self.name)
            self.blackboard.write('quality_report', quality_report, self.name)

            processing_time = time.time() - start_time
            logger.info(f"Quality assurance completed in {processing_time:.2f}s, score: {quality_score}")

            return {
                'success': True,
                'processing_time': processing_time,
                'quality_score': quality_score,
                'outputs': ['quality_score', 'quality_report']
            }

        except Exception as e:
            logger.error(f"Quality assurance failed: {e}")
            raise

    def _assess_quality(self, response: Dict) -> float:
        """Assess response quality based on multiple criteria"""
        score = 1.0

        # Check if response has required components
        if not response.get('summary'):
            score -= 0.4

        if not response.get('themes'):
            score -= 0.3

        if not response.get('citations'):
            score -= 0.2

        # Check summary length (should be substantial)
        summary = response.get('summary', '')
        if len(summary) < 200:
            score -= 0.1

        return max(0.0, score)

    def _generate_quality_report(self, response: Dict, score: float) -> Dict:
        """Generate detailed quality report"""
        return {
            'overall_score': score,
            'has_summary': bool(response.get('summary')),
            'has_themes': bool(response.get('themes')),
            'has_citations': bool(response.get('citations')),
            'summary_length': len(response.get('summary', '')),
            'theme_count': len(response.get('themes', [])),
            'citation_count': len(response.get('citations', []))
        }


class StreamingAgent(BaseAgent):
    """
    Agent responsible for providing real-time updates to users.
    """

    def __init__(self, blackboard: TherapyBlackboard):
        capabilities = AgentCapabilities(
            can_process_parallel=True,
            requires_gpu=False,
            estimated_processing_time=0.1,
            confidence_threshold=1.0,
            fallback_available=False
        )

        super().__init__(
            name="StreamingAgent",
            blackboard=blackboard,
            priority=3,
            capabilities=capabilities
        )

    def can_contribute(self) -> bool:
        """Can always contribute if there are updates to stream"""
        updates = self.blackboard.read('streaming_updates') or []
        last_streamed = getattr(self, 'last_streamed_count', 0)
        return len(updates) > last_streamed

    def get_prerequisites(self) -> List[str]:
        return []

    def get_outputs(self) -> List[str]:
        return ['streaming_response']

    async def contribute(self) -> Dict[str, Any]:
        """Process and format streaming updates"""
        updates = self.blackboard.read('streaming_updates') or []
        last_streamed = getattr(self, 'last_streamed_count', 0)

        new_updates = updates[last_streamed:]
        if new_updates:
            streaming_response = {
                'type': 'progress_update',
                'updates': new_updates,
                'timestamp': time.time()
            }

            self.blackboard.write('streaming_response', streaming_response, self.name)
            self.last_streamed_count = len(updates)

            logger.info(f"Streamed {len(new_updates)} updates")

        return {
            'success': True,
            'updates_streamed': len(new_updates),
            'outputs': ['streaming_response']
        }