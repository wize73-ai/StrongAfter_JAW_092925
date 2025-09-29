import re
from typing import List, Dict, Any
from models.excerpt import Excerpt

def parse_markdown_sections(content: str) -> List[Dict[str, Any]]:
    """
    Parse markdown content into sections.
    Each section is a dictionary with 'title' and 'content' keys.
    """
    # Split content by level 1 headers (# Header)
    sections = re.split(r'^#\s+(.+)$', content, flags=re.MULTILINE)
    
    # The first element is content before any header
    result = []
    current_title = "Introduction"
    current_content = sections[0].strip()
    
    # Process remaining sections
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            # This is a header
            current_title = sections[i].strip()
            current_content = sections[i + 1].strip()
        else:
            # This is the last content section
            current_content = sections[i].strip()
        
        if current_content:
            result.append({
                'title': current_title,
                'content': current_content
            })
    
    return result 