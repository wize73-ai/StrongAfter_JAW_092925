
# Vector-Ready Theme Data – JSON Structure Guide

This document explains the structure of the `strongAfter_themes.json` file, which contains a flattened and metadata-rich representation of trauma-related themes. It is optimized for use in vector databases and AI applications, such as semantic search or retrieval-augmented generation (RAG) pipelines.

## JSON Structure

Each item in the JSON array is an object with the following fields:

- `id`: A unique identifier for the theme or subtheme (hashed for uniqueness).
- `label`: The name/title of the theme or subtheme.
- `description`: A detailed description suitable for semantic embedding and understanding.
- `type`: Indicates the level of the theme:
  - `"parent"` for top-level themes.
  - `"child"` for subthemes nested under a parent theme.
- `related_parent_label`: The label of the parent theme (only applicable for child themes).
- `related_parent_id`: The ID of the parent theme (only applicable for child themes).

## Example Entry

```json
{
  "id": "10c19282",
  "label": "Seeking Support for Addiction",
  "description": "Seeking support for addiction often intersects with addressing the underlying trauma that contributed to it.",
  "type": "child",
  "related_parent_label": "Addiction and Coping Mechanisms",
  "related_parent_id": "2516db5a"
}
```

## Differentiating Theme Levels

- To find all **parent themes**, filter where `type == "parent"`.
- To find all **child themes**, filter where `type == "child"`.

## Mapping Parent-Child Relationships

- Use `related_parent_label` or `related_parent_id` to associate a child theme back to its parent.
- Parent themes do not contain any `related_parent_label` or `related_parent_id` values.

## Use Cases

This structure is ideal for:
- Creating semantic search indices where each item can be embedded independently.
- Reconstructing hierarchical views using parent-child mappings.
- Grouping or filtering themes based on their level or relational context.

## File Location

The JSON file can be found at:

```
vector_ready_themes_final.json
```
