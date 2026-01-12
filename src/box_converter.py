r"""
Module for converting tcolorbox environments in LaTeX to MDX/KaTeX format.

Converts the \begin{tcolorbox} and \end{tcolorbox} commands to be compatible with MDX/KaTeX.
"""
import re
from typing import List, Tuple
from math_converter import MathConverter

class BoxConverter:
    def __init__(self):
        self.box_types = {
            'dem_box': 'DemBox',
            'ejem_box': 'EjemBox',
            'ej_box': 'EjBox',
        }
        
        # No usar regex directamente, procesar manualmente para manejar llaves anidadas
        self.box_start_pattern = re.compile(r'\\begin\{(\w+_box)\}\{')

    def extract_title_with_nested_braces(self, content: str, start_pos: int) -> tuple:
        """Extract title handling nested braces correctly.
        
        Args:
            content: Full content string
            start_pos: Position after the opening { of the title
            
        Returns:
            tuple: (title, end_position)
        """
        depth = 1
        i = start_pos
        title_chars = []
        
        while i < len(content) and depth > 0:
            if content[i] == '\\' and i + 1 < len(content):
                # Escape sequence, add both characters
                title_chars.append(content[i:i+2])
                i += 2
                continue
            elif content[i] == '{':
                depth += 1
                title_chars.append(content[i])
            elif content[i] == '}':
                depth -= 1
                if depth > 0:
                    title_chars.append(content[i])
            else:
                title_chars.append(content[i])
            i += 1
        
        return ''.join(title_chars), i

    def convert_boxes(self, match) -> str:
        """Convert a tcolorbox LaTeX environment to MDX/KaTeX format.

        Args:
            match: Regex match object for the tcolorbox.

        Returns:
            str: Converted box in MDX/KaTeX format.
        """
        box_type = match.group(1)
        title = match.group(2)
        content = match.group(3).strip()
        
        mdx_box_type = self.box_types.get(box_type, 'Box')
        
        # Escapar comillas dobles en el título para no romper el atributo HTML
        title_escaped = title.replace('"', '&quot;')
        
        return f"<{mdx_box_type} title=\"{title_escaped}\">\n\n{content}\n\n</{mdx_box_type}>"
    
    def convert(self, content: str, max_depth: int = 10) -> str:
        """Convert all tcolorbox environments in the content, including nested boxes.

        Args:
            content (str): Content to be processed.
            max_depth (int): Maximum recursion depth to prevent infinite loops.

        Returns:
            str: Content with converted tcolorbox environments.
        """
        if max_depth <= 0:
            return content
            
        result = []
        pos = 0
        has_changes = False
        
        while True:
            # Find next box start
            match = self.box_start_pattern.search(content, pos)
            if not match:
                # No more boxes, add remaining content
                result.append(content[pos:])
                break
            
            # Add content before this box
            result.append(content[pos:match.start()])
            
            box_type = match.group(1)
            title_start = match.end()
            
            # Extract title with nested braces
            title, title_end = self.extract_title_with_nested_braces(content, title_start)
            
            # Find the end of the box
            end_pattern = f'\\end{{{box_type}}}'
            end_pos = content.find(end_pattern, title_end)
            
            if end_pos == -1:
                # No matching end found, just continue
                result.append(match.group(0))
                pos = match.end()
                continue
            
            # Extract box content
            box_content = content[title_end:end_pos].strip()
            
            # Recursively convert nested boxes in the content
            box_content_converted = self.convert(box_content, max_depth - 1)
            
            # Get MDX box type
            mdx_box_type = self.box_types.get(box_type, 'Box')
            
            # Escape quotes in title
            title_escaped = title.replace('"', '&quot;')
            
            # Build the converted box
            converted = f"<{mdx_box_type} title=\"{title_escaped}\">\n\n{box_content_converted}\n\n</{mdx_box_type}>"
            result.append(converted)
            has_changes = True
            
            # Move position past the end tag
            pos = end_pos + len(end_pattern)
        
        final_result = ''.join(result)
        
        # If we made changes, check if there are more boxes to convert at the same level
        # (in case boxes were at the same nesting level)
        if has_changes and max_depth > 0:
            # Check if there are still unconverted boxes
            if self.box_start_pattern.search(final_result):
                return self.convert(final_result, max_depth - 1)
        
        return final_result