import pytest
from utils.markdown_parser import parse_markdown_sections, chunk_text

def test_basic_section_parsing():
    markdown = """# Section 1
Description

# Section 2
Text4"""
    
    expected = {
        "Section 1": {
            "contents": ["Description"]
        },
        "Section 2": {
            "contents": ["Text4"]
        }
    }
    
    assert parse_markdown_sections(markdown) == expected

def test_nested_section_parsing():
    markdown = """# Section 1
Description

## Subsection 1a
Text

## Subsection 1b
Text2

Text3

# Section 2
Text4"""
    
    expected = {
        "Section 1": {
            "Subsection 1a": {
                "contents": ["Text"]
            },
            "Subsection 1b": {
                "contents": ["Text2", "Text3"]
            },
            "contents": ["Description"]
        },
        "Section 2": {
            "contents": ["Text4"]
        }
    }
    
    assert parse_markdown_sections(markdown) == expected

def test_empty_sections():
    markdown = """# Section 1

## Subsection 1a

# Section 2"""
    
    expected = {
        "Section 1": {
            "Subsection 1a": {
                "contents": []
            },
            "contents": []
        },
        "Section 2": {
            "contents": []
        }
    }
    
    assert parse_markdown_sections(markdown) == expected

def test_multiline_content():
    markdown = """# Section 1
Line 1
Line 2
Line 3

## Subsection 1a
Subsection line 1
Subsection line 2"""
    
    expected = {
        "Section 1": {
            "Subsection 1a": {
                "contents": ["Subsection line 1", "Subsection line 2"]
            },
            "contents": ["Line 1", "Line 2", "Line 3"]
        }
    }
    
    assert parse_markdown_sections(markdown) == expected

def test_text_chunking():
    text = """Line 1
Line 2
Line 3
Line 4
Line 5
Line 6
Line 7"""
    chunks = chunk_text(text)
    
    # Should create 3 chunks with 2-line overlap
    assert len(chunks) == 3
    
    # First chunk: lines 0-3
    assert "Line 1" in chunks[0]
    assert "Line 4" in chunks[0]
    
    # Second chunk: lines 2-5
    assert "Line 3" in chunks[1]
    assert "Line 6" in chunks[1]
    
    # Third chunk: lines 4-7
    assert "Line 5" in chunks[2]
    assert "Line 7" in chunks[2]

def test_text_chunking_short_text():
    text = """Line 1
Line 2"""
    chunks = chunk_text(text)
    
    # Should return empty list for text with fewer than 2 lines
    assert len(chunks) == 0 