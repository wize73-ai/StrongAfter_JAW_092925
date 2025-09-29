"""
StrongAfter Trauma Recovery Assistant - Blackboard Architecture
================================================================

Flask application implementing a multi-agent blackboard system for
parallel processing and improved therapeutic response performance.

Author: JAWilson
Created: September 2025
License: Proprietary - StrongAfter Systems

This implementation provides:
- Multi-agent processing with parallel execution
- Real-time streaming responses via Server-Sent Events
- Quality assurance with therapeutic standards preservation
- Hybrid LLM architecture for optimal cost/performance balance
"""

import json
import os
import time
import logging
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json
import google.generativeai as genai

# Import blackboard components
from blackboard import (
    TherapyBlackboard,
    BlackboardControlStrategy,
    ThemeAnalysisAgent,
    ExcerptRetrievalAgent,
    SummaryGenerationAgent,
    QualityAssuranceAgent,
    StreamingAgent
)
from blackboard.local_llm_agent import LocalLLMAgent, LocalLLMConfig


# Load environment variables
load_dotenv(verbose=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import existing utilities
from utils.markdown_parser import parse_markdown_sections


def load_themes_and_metadata() -> tuple[list[dict], dict]:
    """Load themes and their corresponding excerpts from retrievals."""
    resources_path = os.path.join(os.path.dirname(__file__), 'resources')

    # Load themes
    themes_path = os.path.join(resources_path, 'strongAfter_themes.json')
    with open(themes_path, 'r', encoding='utf-8') as f:
        themes = json.load(f)
    logger.info(f"Loaded {len(themes)} themes from JSON")

    # Load retrievals
    retrievals_path = os.path.join(resources_path, 'generated', 'retrievals.json')
    with open(retrievals_path, 'r', encoding='utf-8') as f:
        retrievals = json.load(f)
    logger.info(f"Loaded retrievals data with {len(retrievals)} entries")

    # Load book metadata
    try:
        metadata_path = os.path.join(resources_path, 'book_metadata.json')
        with open(metadata_path, 'r', encoding='utf-8') as f:
            book_metadata = json.load(f)
        logger.info(f"Loaded book metadata for {len(book_metadata)} sources")
    except FileNotFoundError:
        logger.warning("Book metadata file not found, using empty metadata")
        book_metadata = {}

    # Add excerpts to themes
    for theme in themes:
        theme_label = theme['label']
        if theme_label in retrievals:
            theme['excerpts'] = retrievals[theme_label]['similar_excerpts']
        else:
            logger.warning(f"No retrievals found for theme {theme_label}")
            theme['excerpts'] = []

    return themes, book_metadata


class BlackboardTherapyService:
    """
    Main service class that orchestrates the blackboard system
    """

    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Load data
        self.themes_data, self.book_metadata = load_themes_and_metadata()

        # Initialize blackboard system
        self.blackboard = None
        self.control_strategy = None
        self.agents = {}

        # Initialize system
        self._initialize_system()

    def _initialize_system(self):
        """Initialize the blackboard system with agents"""
        logger.info("Initializing blackboard therapy system...")

        # Create blackboard
        self.blackboard = TherapyBlackboard()

        # Initialize local LLM agent
        local_llm_config = LocalLLMConfig(
            host="localhost",
            port=11434,
            model_name="llama3.1:8b",
            timeout=30.0,
            temperature=0.1
        )

        # Create agents
        self.agents = {
            'local_llm': LocalLLMAgent(self.blackboard, local_llm_config),
            'theme_analysis': ThemeAnalysisAgent(self.blackboard, self.gemini_model),
            'excerpt_retrieval': ExcerptRetrievalAgent(self.blackboard),
            'summary_generation': SummaryGenerationAgent(
                self.blackboard,
                self.gemini_model,
                self.book_metadata
            ),
            'quality_assurance': QualityAssuranceAgent(self.blackboard),
            'streaming': StreamingAgent(self.blackboard)
        }

        # Create control strategy
        self.control_strategy = BlackboardControlStrategy(
            self.blackboard,
            list(self.agents.values()),
            self.themes_data
        )

        logger.info("Blackboard system initialized successfully")

    async def process_text_async(self, text: str) -> Dict[str, Any]:
        """
        Process text using the blackboard system

        Args:
            text: User input text

        Returns:
            Processing results
        """
        if not text.strip():
            raise ValueError("No text provided")

        logger.info(f"Processing text with blackboard system: {text[:100]}...")

        try:
            # Clear previous state
            self.blackboard.clear()

            # Update themes data on blackboard
            self.blackboard.write('theme_candidates', self.themes_data, 'BlackboardService')

            # Execute using hybrid strategy for optimal performance
            from blackboard.control_strategy import ExecutionStrategy
            results = await self.control_strategy.execute(
                text,
                strategy=ExecutionStrategy.HYBRID
            )

            return results

        except Exception as e:
            logger.error(f"Error in blackboard processing: {e}", exc_info=True)
            raise

    def process_text_sync(self, text: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for async processing

        Args:
            text: User input text

        Returns:
            Processing results
        """
        # Create new event loop for this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(self.process_text_async(text))
            return result
        finally:
            loop.close()

    def get_system_status(self) -> Dict[str, Any]:
        """Get status of the blackboard system"""
        agent_status = {}
        for name, agent in self.agents.items():
            try:
                agent_status[name] = agent.get_status()
            except Exception as e:
                agent_status[name] = {'error': str(e)}

        return {
            'blackboard_state': self.blackboard.get_state_summary() if self.blackboard else None,
            'agents': agent_status,
            'control_strategy_metrics': self.control_strategy.get_metrics() if self.control_strategy else None,
            'themes_loaded': len(self.themes_data),
            'metadata_sources': len(self.book_metadata)
        }

    async def health_check_async(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            'overall': 'healthy',
            'components': {},
            'timestamp': time.time()
        }

        # Check Gemini API
        try:
            test_response = self.gemini_model.generate_content("Test")
            health_status['components']['gemini'] = {
                'status': 'healthy',
                'response_time': 0.5  # Placeholder
            }
        except Exception as e:
            health_status['components']['gemini'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall'] = 'degraded'

        # Check local LLM if available
        try:
            local_llm_health = await self.agents['local_llm'].health_check()
            health_status['components']['local_llm'] = local_llm_health
            if not local_llm_health.get('available', False):
                health_status['overall'] = 'degraded'
        except Exception as e:
            health_status['components']['local_llm'] = {
                'status': 'unhealthy',
                'error': str(e)
            }

        # Check data availability
        health_status['components']['data'] = {
            'themes_count': len(self.themes_data),
            'metadata_count': len(self.book_metadata),
            'status': 'healthy' if self.themes_data else 'unhealthy'
        }

        return health_status


# Initialize the service
therapy_service = BlackboardTherapyService()

# Create Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:4200", "http://localhost:4201", "http://localhost:4202"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with comprehensive system status"""
    try:
        # Run async health check
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            health_status = loop.run_until_complete(therapy_service.health_check_async())
        finally:
            loop.close()

        return jsonify(health_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'overall': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 500


@app.route('/api/process-text', methods=['POST'])
def process_text():
    """Main text processing endpoint using blackboard system"""
    logger.info("Received process-text request")
    start_time = time.time()

    try:
        data = request.get_json()
        text = data.get('text', '')

        if not text.strip():
            logger.warning("No text provided in request")
            return jsonify({'error': 'No text provided'}), 400

        # Process using blackboard system
        results = therapy_service.process_text_sync(text)

        # Transform themes to match frontend expectations
        formatted_themes = []
        for theme in results.get('themes', []):
            # Add frontend-compatible fields
            formatted_theme = theme.copy()
            formatted_theme['is_relevant'] = True  # All returned themes are relevant
            formatted_theme['score'] = theme.get('relevance_score', 0.0)
            formatted_themes.append(formatted_theme)

        # Format response for frontend compatibility
        response_data = {
            'original': text,
            'themes': formatted_themes,
            'summary': results.get('summary', ''),
            'processing_time': results.get('processing_time', 0),
            'blackboard_metrics': results.get('blackboard_metrics', {}),
            'quality_score': results.get('quality_score'),
            'book_metadata': therapy_service.book_metadata
        }

        # Add streaming updates if available
        if 'streaming_updates' in results:
            response_data['streaming_updates'] = results['streaming_updates']

        logger.info(f"Successfully processed text in {time.time() - start_time:.2f}s")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error processing text: {e}", exc_info=True)
        return jsonify({
            'error': 'Error processing text with AI',
            'details': str(e),
            'processing_time': time.time() - start_time
        }), 500


@app.route('/api/process-text-stream', methods=['POST'])
def process_text_stream():
    """Streaming endpoint for real-time processing updates"""
    logger.info("Received streaming process-text request")

    try:
        data = request.get_json()
        text = data.get('text', '')

        if not text.strip():
            return Response(
                "data: " + json.dumps({"error": "No text provided"}) + "\n\n",
                mimetype='text/plain'
            )

        def generate_stream():
            """Generator function for streaming updates"""
            try:
                # Send initial status
                yield "data: " + json.dumps({
                    "type": "status",
                    "message": "Starting analysis...",
                    "progress": 10
                }) + "\n\n"

                # Analyze themes
                yield "data: " + json.dumps({
                    "type": "status",
                    "message": "Analyzing themes...",
                    "progress": 30
                }) + "\n\n"

                # Process using blackboard system
                yield "data: " + json.dumps({
                    "type": "status",
                    "message": "Processing with AI agents...",
                    "progress": 50
                }) + "\n\n"

                # Get results
                results = therapy_service.process_text_sync(text)

                yield "data: " + json.dumps({
                    "type": "status",
                    "message": "Generating summary...",
                    "progress": 80
                }) + "\n\n"

                # Format final response
                formatted_themes = []
                for theme in results.get('themes', []):
                    formatted_theme = theme.copy()
                    formatted_theme['is_relevant'] = True
                    formatted_theme['score'] = theme.get('relevance_score', 0.0)
                    formatted_themes.append(formatted_theme)

                final_response = {
                    'original': text,
                    'themes': formatted_themes,
                    'summary': results.get('summary', ''),
                    'processing_time': results.get('processing_time', 0),
                    'blackboard_metrics': results.get('blackboard_metrics', {}),
                    'quality_score': results.get('quality_score'),
                    'book_metadata': therapy_service.book_metadata
                }

                # Send final results
                yield "data: " + json.dumps({
                    "type": "complete",
                    "progress": 100,
                    "data": final_response
                }) + "\n\n"

            except Exception as e:
                logger.error(f"Error in streaming: {e}", exc_info=True)
                yield "data: " + json.dumps({
                    "type": "error",
                    "message": str(e)
                }) + "\n\n"

        return Response(
            generate_stream(),
            mimetype='text/plain',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': 'http://localhost:4200',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )

    except Exception as e:
        logger.error(f"Error setting up stream: {e}", exc_info=True)
        return Response(
            "data: " + json.dumps({"type": "error", "message": str(e)}) + "\n\n",
            mimetype='text/plain'
        )


@app.route('/api/system-status', methods=['GET'])
def system_status():
    """Get detailed system status"""
    try:
        status = therapy_service.get_system_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/parsed-book', methods=['GET'])
def get_parsed_book():
    """Get parsed book content (existing endpoint for compatibility)"""
    try:
        # Get the first markdown file from the resources/books directory
        books_dir = os.path.join(os.path.dirname(__file__), 'resources', 'books')
        markdown_files = [f for f in os.listdir(books_dir) if f.endswith('.md')]

        if not markdown_files:
            return jsonify({"error": "No markdown files found"}), 404

        # Process the first book
        book_filename = markdown_files[0]
        file_path = os.path.join(books_dir, book_filename)

        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Parse the markdown content
        sections = parse_markdown_sections(content)

        # Add filename to each section
        for section in sections:
            section['filename'] = book_filename

        return jsonify(sections)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/agents/status', methods=['GET'])
def get_agents_status():
    """Get status of all agents"""
    try:
        agent_status = {}
        for name, agent in therapy_service.agents.items():
            agent_status[name] = agent.get_status()

        return jsonify({
            'agents': agent_status,
            'total_agents': len(therapy_service.agents),
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get system performance metrics"""
    try:
        metrics = {
            'blackboard': therapy_service.blackboard.get_metrics(),
            'control_strategy': therapy_service.control_strategy.get_metrics(),
            'agents': {
                name: agent.metrics for name, agent in therapy_service.agents.items()
            }
        }
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting StrongAfter Blackboard System...")
    print(f"Loaded {len(therapy_service.themes_data)} themes")
    print(f"Initialized {len(therapy_service.agents)} agents")
    print("=" * 50)

    app.run(debug=True, port=5002)