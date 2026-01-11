"""
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
        
        self.box_pattern = re.compile(
            r'\\begin\{(\w+_box)\}\{([^}]*)\}(.*?)\\end\{\1\}',
            re.DOTALL
        )

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
        
        return f"<{mdx_box_type} title=\"{title}\">\n\n{content}\n\n</{mdx_box_type}>"
    
    def convert(self,  content: str) -> str:
        """Convert all tcolorbox environments in the content.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with converted tcolorbox environments.
        """
        return self.box_pattern.sub(self.convert_boxes, content)