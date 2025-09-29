"""
StrongAfter Trauma Recovery Assistant - Legacy Flask Application
================================================================

Original Flask application providing trauma recovery assistance with
theme analysis, excerpt retrieval, and therapeutic response generation.

Author: JAWilson
Created: September 2025
License: Proprietary - StrongAfter Systems

This is the baseline implementation for comparison with the blackboard
architecture system. Provides traditional sequential processing with
APA-Lite citation formatting and therapeutic content analysis.
"""

import json
import os
import time
from dotenv import load_dotenv
import logging

load_dotenv(verbose=True)

from flask import Flask, jsonify, request
from flask_cors import CORS
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import custom modules
from utils.markdown_parser import parse_markdown_sections


def load_themes() -> tuple[list[dict], dict]:
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
    metadata_path = os.path.join(resources_path, 'book_metadata.json')
    with open(metadata_path, 'r', encoding='utf-8') as f:
        book_metadata = json.load(f)
    logger.info(f"Loaded book metadata for {len(book_metadata)} sources")
    
    # Add excerpts to themes
    for theme in themes:
        theme_label = theme['label']
        if theme_label in retrievals:
            theme['excerpts'] = retrievals[theme_label]['similar_excerpts']
        else:
            raise Exception(f"No retrievals found for theme {theme_label}")
    
    return themes, book_metadata

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
MODEL = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

# Load themes with their excerpts
THEMES_DATA, BOOK_METADATA = load_themes()

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:4200"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Backend is running'
    })

def summarize_excerpts(themes: list[dict], all_excerpts: list, user_text: str) -> str:
    """Generate a single summary of excerpts for all relevant themes using the LLM."""
    if not all_excerpts or not themes:
        return ""
    
    # Extract theme information
    themes_info = []
    for theme in themes:
        themes_info.append(f"- {theme['label']}: {theme['description']}")
    
    themes_text = "\n".join(themes_info)
    
    # Prepare excerpts for the prompt with source information and APA metadata
    excerpts_text = ""
    references_list = []
    unique_sources = {}
    reference_counter = 1
    
    for i, item in enumerate(all_excerpts, 1):
        excerpt = item['excerpt']
        book_url = excerpt.get('book_url', '')
        title = excerpt.get('title', 'Unknown Source')
        
        # Find the filename to get metadata
        filename = None
        for key in BOOK_METADATA.keys():
            # Match by checking if title components are in the filename
            title_words = title.replace('Chapter ', 'Chapter_').replace(' ', '_')
            if title_words in key or title in key:
                filename = key
                break
        
        # Get APA citation info
        if filename and filename in BOOK_METADATA:
            metadata = BOOK_METADATA[filename]
            apa_citation = f"{metadata['author']} ({metadata['year']}). *{metadata['title']}*. {metadata['publisher']}."
            purchase_url = metadata['purchase_url']
        else:
            apa_citation = f"Unknown Author. *{title}*."
            purchase_url = "http://strongafter.org"
        
        excerpts_text += f"EXCERPT {i} (Source: {apa_citation}):\n{excerpt['text']}\n\n"
        
        # Add to references if not already included
        if apa_citation not in unique_sources:
            unique_sources[apa_citation] = reference_counter
            # Create superscript number using Unicode
            superscript_num = str(reference_counter).translate(str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹'))
            references_list.append(f"{superscript_num} {apa_citation} [Get this book]({purchase_url})")
            reference_counter += 1
    
    # Create references section
    references_text = "\n".join(references_list)
    
    # Create prompt for the LLM
    prompt = f"""You are a trauma recovery assistant helping to summarize information related to recovery themes.

USER'S ORIGINAL INPUT (for context only - DO NOT directly reference, quote, or mention this in your response):
"{user_text}"

RELEVANT THEMES:
{themes_text}

I have found several relevant passages that relate to these themes. Please provide a comprehensive ~2 paragraph summary that:
1. Synthesizes the key insights from these passages across all the relevant themes
2. Explains how the passages relate to the themes and to each other
3. Cites specific passages by quoting them using markdown indentation format when referencing content, with the full passage being italicized. Prefer to use quotes in this format, rather than inline.
4. Use numbered superscript citations like ⁽¹⁾ or ⁽²⁾ when referencing specific excerpts (where the number corresponds to the excerpt number). ALWAYS use this exact format with parenthetical superscript numbers. 
   IMPORTANT: If multiple excerpts apply to the same point, list them as separate citations, e.g., ⁽¹⁾⁽²⁾ or ⁽³⁾⁽⁴⁾, NOT as grouped citations like ⁽¹,²⁾.
5. Provides a cohesive narrative that connects the themes and insights
6. Keep the user's original input in mind for context, but NEVER directly reference, quote, or mention it in your response
7. Try to incorporate 2-3 quotes from the excerpts in to your summary, but only as useful. Prefer to include them in indented markdown format, with longer quotes (1-3 sentences), rather than small sentence fragements.

IMPORTANT: When citing sources, ALWAYS use superscript numbers in parentheses like ⁽¹⁾ ⁽²⁾ ⁽³⁾ ⁽⁴⁾ ⁽⁵⁾. Do not use ^[1]^ or [1] or (1) or any other format. EACH citation must be separate parenthetical superscript numbers.

After your summary, include a References section with APA-Lite citations and 'Get this book' links.

Paragraphs should be kept short and concise, introducing whitespace and formatting to make them easier to read when helpful.

Here are the passages:

{excerpts_text}

Your summary should be helpful for someone who is recovering from trauma and seeking to understand how these themes work together in their recovery journey. Write as if you are speaking directly to someone on their healing path, using supportive and therapeutic language.

End your response with:

## References
{references_text}
"""

    # Call the LLM to generate the summary
    try:
        response = MODEL.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating combined summary: {e}")
        return f"Unable to generate summary due to an error: {str(e)}"

def get_theme_excerpts(theme_id: str, max_excerpts: int = 3) -> list[dict]:
    """Get the most relevant excerpts for a given theme."""
    # Find the theme by ID
    theme = next((t for t in THEMES_DATA if t['id'] == theme_id), None)
    if not theme:
        raise Exception(f"Theme with ID {theme_id} not found")
    
    # Get excerpts for this theme
    excerpts = theme.get('excerpts', [])
    logger.info(f"Found {len(excerpts)} excerpts for theme {theme['label']}")
    
    top_excerpts = excerpts[:max_excerpts]
    logger.info(f"Returning top {len(top_excerpts)} excerpts for theme {theme['label']}")
    
    if not top_excerpts:
        breakpoint()
        raise Exception(f"No excerpts found for theme {theme['label']}")
    
    return top_excerpts

def rank_themes(text: str, themes: list[dict]) -> list[dict]:
    """Rank all themes and select the most relevant ones using a single LLM call."""
    logger.info(f"Ranking themes for text: {text[:100]}...")
    logger.info(f"Number of themes to analyze: {len(themes)}")
    
    # Create a numbered list of themes for the prompt
    themes_list = "\n".join([
        f"{i+1}. {theme['label']}: {theme['description']}"
        for i, theme in enumerate(themes)
    ])
    
    prompt = f"""You are a specialized AI for trauma recovery analysis. Your task is to analyze how well each theme relates to the user's text input and select the 1-3 most relevant themes.

THEMES TO ANALYZE:
{themes_list}

USER INPUT:
"{text}"

INSTRUCTIONS:
1. For each theme, provide:
   - A brief analysis (1-2 sentences) explaining how it relates to the text
   - A relevance score from 0-100 using these guidelines:
     100 - Theme perfectly captures the main point
     90 - Theme is a primary focus
     85 - Theme is explicitly discussed in detail
     80 - Theme is directly mentioned
     70 - Parts of theme are mentioned
     60 - Theme is alluded to
     50 - Theme is tangentially related
     40 - Theme shares some concepts
     30 - Theme has weak connection
     20 - Theme is unrelated except for sexual assault context
     10 - Theme is unrelated except for adjacent topics
     0 - Theme is completely unrelated

2. Select the 1-3 most relevant themes (those with highest scores)

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
Theme 1:
Analysis: [Your analysis]
Score: [0-100]

Theme 2:
Analysis: [Your analysis]
Score: [0-100]

[Continue for all themes...]

Most Relevant Themes: [List the numbers of the 1-3 most relevant themes, e.g. "1, 2"]"""

    try:
        logger.info("Sending request to Gemini API...")
        start_time = time.time()
        response = MODEL.generate_content(prompt)
        end_time = time.time()
        logger.info(f"LLM response time: {end_time - start_time:.2f} seconds")
        content = response.text.strip()
        logger.info("Received response from Gemini API")
        logger.debug(f"Raw API response:\n{content}")
        
        # Parse the response
        theme_analyses = {}
        most_relevant = []
        
        # Split into sections
        sections = content.split('\n\n')
        logger.info(f"Split response into {len(sections)} sections")
        
        # Find the most relevant themes section first
        most_relevant_section = next((s for s in sections if s.startswith('Most Relevant Themes:')), None)
        if most_relevant_section:
            # Extract theme numbers
            theme_nums = [int(n.strip()) - 1 for n in most_relevant_section.split(':')[1].strip().split(',')]
            most_relevant = [themes[n]['id'] for n in theme_nums if n < len(themes)]
            logger.info(f"Found {len(most_relevant)} most relevant themes: {most_relevant}")
        else:
            logger.warning("No 'Most Relevant Themes' section found in response")
        
        # Process each theme section
        for section in sections:
            if section.startswith('Theme '):
                # Extract theme number
                theme_num = int(section.split(':')[0].split(' ')[1]) - 1
                if theme_num < len(themes):
                    theme = themes[theme_num]
                    
                    # Extract analysis and score
                    analysis = section.split('Analysis:')[1].split('Score:')[0].strip()
                    score = int(section.split('Score:')[1].strip())
                    
                    # Create theme data
                    theme_data = theme.copy()
                    theme_data['analysis'] = analysis
                    theme_data['score'] = score
                    theme_data['is_relevant'] = theme['id'] in most_relevant
                    
                    # Add excerpts for relevant themes
                    if theme_data['is_relevant']:
                        theme_data['excerpts'] = get_theme_excerpts(theme['id'])
                    else:
                        theme_data['excerpts'] = []
                    
                    theme_analyses[theme['id']] = theme_data
                    logger.debug(f"Processed theme {theme_num + 1}: {theme['label']} (score: {score}, relevant: {theme_data['is_relevant']})")
        
        # Convert to list and sort by score
        ranked_themes = list(theme_analyses.values())
        ranked_themes.sort(key=lambda x: x['score'], reverse=True)
        
        # Generate a single summary for all relevant themes
        relevant_themes = [t for t in ranked_themes if t['is_relevant']]
        if relevant_themes:
            # Collect all excerpts from relevant themes
            all_excerpts = []
            for theme in relevant_themes:
                all_excerpts.extend(theme.get('excerpts', []))
            
            # Generate single summary
            combined_summary = summarize_excerpts(relevant_themes, all_excerpts, text)
            
            # Add the combined summary to all relevant themes
            for theme in ranked_themes:
                if theme['is_relevant']:
                    theme['excerpt_summary'] = combined_summary
                else:
                    theme['excerpt_summary'] = ""
        
        logger.info(f"Returning {len(ranked_themes)} ranked themes")
        logger.debug(f"Ranked themes: {json.dumps(ranked_themes, indent=2)}")
        
        return ranked_themes
        
    except Exception as e:
        logger.error(f"Error ranking themes: {e}", exc_info=True)
        # Return empty list on error
        return []

@app.route('/api/process-text', methods=['POST'])
def process_text():
    logger.info("Received process-text request")
    data = request.get_json()
    text = data.get('text', '')
    
    if not text.strip():
        logger.warning("No text provided in request")
        return jsonify({
            'error': 'No text provided'
        }), 400

    try:
        start_time = time.time()
        # Rank all themes at once
        ranked_themes = rank_themes(text, THEMES_DATA)
        logger.info(f"Successfully processed text, found {len(ranked_themes)} themes")
        
        # Get relevant themes (those with is_relevant=True)
        relevant_themes = [theme for theme in ranked_themes if theme.get('is_relevant', False)]
        
        # Generate summary with citations for relevant themes
        summary = ""
        if relevant_themes:
            all_excerpts = []
            for theme in relevant_themes:
                if 'excerpts' in theme and theme['excerpts']:
                    all_excerpts.extend(theme['excerpts'])
            
            summary = summarize_excerpts(relevant_themes, all_excerpts, text)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        response = {
            'original': text,
            'themes': ranked_themes,
            'summary': summary,
            'processing_time': processing_time,
            'book_metadata': BOOK_METADATA
        }
        logger.debug(f"Sending response: {json.dumps(response, indent=2)}")
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error processing text: {e}", exc_info=True)
        return jsonify({
            'error': 'Error processing text with AI'
        }), 500

@app.route('/api/parsed-book', methods=['GET'])
def get_parsed_book():
    try:
        # Get the first markdown file from the resources/books directory
        books_dir = os.path.join(os.path.dirname(__file__), 'resources', 'books')
        markdown_files = [f for f in os.listdir(books_dir) if f.endswith('.md')]
        
        if not markdown_files:
            return jsonify({"error": "No markdown files found"}), 404
        
        # For simplicity, let's process only the first book found.
        # In a real application, you might want to specify which book or process all.
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

if __name__ == '__main__':
    import sys
    port = 5001 if '--port' not in sys.argv else int(sys.argv[sys.argv.index('--port') + 1])
    app.run(debug=True, port=port) 