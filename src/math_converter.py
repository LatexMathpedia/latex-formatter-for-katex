"""
Conversor for mathematical expressions in LaTeX to MDX/KaTeX format.

This module manages the conversion of mathematical delimiter and
secures the compatibility between LaTeX and MDX/KaTeX formats.
"""

import re
from typing import List, Tuple

class MathConverter:
    """
    A class to convert LaTeX mathematical expressions to MDX/KaTeX format.
    """
    
    def __init__(self):
        """Initialize the MathConverter with regex patterns for delimiters."""
        self.inline_paren_pattern = re.compile(r'\\[(](.*?)\\[)]', re.DOTALL)
        self.display_bracket_pattern = re.compile(r'\\\[(.*?)\\\]', re.DOTALL)
        
        # Patterns for various LaTeX math environments
        self.align_pattern = re.compile(
            r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}',
            re.DOTALL
        )
        self.equation_pattern = re.compile(
            r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}',
            re.DOTALL
        )
        self.gather_pattern = re.compile(
            r'\\begin\{gather\*?\}(.*?)\\end\{gather\*?\}',
            re.DOTALL
        )
        self.multline_pattern = re.compile(
            r'\\begin\{multline\*?\}(.*?)\\end\{multline\*?\}',
            re.DOTALL
        )
        
        # Pattern for maths in already converted format
        # Nota: Permitimos \\ antes del cierre $$ porque en LaTeX se usa para saltos de línea
        self.already_inline_pattern = re.compile(r'(?<!\\)\$(?!\$)(.*?)(?<!\\)\$(?!\$)', re.DOTALL)
        self.already_display_pattern = re.compile(r'(?<!\\)\$\$(.*?)(\\\\)?\$\$', re.DOTALL)
        
    def protect_existing_math(self, content: str) -> Tuple[str, List[str]]:
        """Protects the maths already in MDX/KaTeX format for avoiding double conversion.

        Args:
            content (str): Content to be processed.

        Returns:
            Tuple[str, List[str]]: Processed content and list of protected maths.
        """
        protected_blocks = []
        
        # IMPORTANTE: Proteger display math PRIMERO ($$...$$) antes que inline ($...$)
        # para evitar que los $ de $$ sean capturados como inline
        def protect_display(match):
            # El grupo 1 es el contenido, el grupo 2 es \\ opcional antes del cierre
            content_math = match.group(1)
            backslashes = match.group(2) if match.group(2) else ""
            protected_blocks.append(f"$${content_math}{backslashes}$$")
            return f"__PROTECTED_MATH_{len(protected_blocks) - 1}__"
        
        content = self.already_display_pattern.sub(protect_display, content)
        
        # Ahora proteger inline math
        def protect_inline(match):
            protected_blocks.append(f"${match.group(1)}$")
            return f"__PROTECTED_MATH_{len(protected_blocks) - 1}__"
        
        content = self.already_inline_pattern.sub(protect_inline, content)
        
        return content, protected_blocks
    
    def restore_protected_math(self, content: str, protected_blocks: List[str]) -> str:
        """Restores the protected maths back into the content.

        Args:
            content (str): Content to be processed.
            protected_blocks (List[str]): List of protected maths.

        Returns:
            str: Content with restored maths.
        """
        for i, block in enumerate(protected_blocks):
            content = content.replace(f"__PROTECTED_MATH_{i}__", block)
        return content
    
    def convert_inline_math(self, content: str) -> str:
        """Converts LaTeX inline math delimiters to MDX/KaTeX format.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with converted inline math.
        """
        def replacer(match):
            math_content = match.group(1)
            math_content = math_content.strip()
            return f"${math_content}$"
        
        return self.inline_paren_pattern.sub(replacer, content)
    
    def convert_display_math(self, content: str) -> str:
        """Converts LaTeX display math delimiters to MDX/KaTeX format.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with converted display math.
        """
        def replacer(match):
            math_content = match.group(1)
            math_content = math_content.strip()
            return f"$$\n{math_content}\n$$"
        
        return self.display_bracket_pattern.sub(replacer, content)
    

    def convert_align_environment(self, content: str) -> str:
        """Converts LaTeX align environments to MDX/KaTeX format.
        Keeps the \begin{align*}...\end{align*} inside $$ delimiters.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with converted align environments.
        """
        def replacer(match):
            # Keep the full match including \begin{align*}...\end{align*}
            return f"$$\n{match.group(0)}\n$$"
        
        return self.align_pattern.sub(replacer, content)
    
    def convert_equation_environment(self, content: str) -> str:
        """Converts LaTeX equation environments to MDX/KaTeX format.
        Keeps the \begin{equation*}...\end{equation*} inside $$ delimiters.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with converted equation environments.
        """
        def replacer(match):
            # Keep the full match including \begin{equation*}...\end{equation*}
            return f"$$\n{match.group(0)}\n$$"
        
        return self.equation_pattern.sub(replacer, content)
    
    def convert_gather_environment(self, content: str) -> str:
        """Converts LaTeX gather environments to MDX/KaTeX format.
        Keeps the \begin{gather*}...\end{gather*} inside $$ delimiters.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with converted gather environments.
        """
        def replacer(match):
            # Keep the full match including \begin{gather*}...\end{gather*}
            return f"$$\n{match.group(0)}\n$$"
        
        return self.gather_pattern.sub(replacer, content)
    
    def convert_multline_environment(self, content: str) -> str:
        """Converts LaTeX multline environments to MDX/KaTeX format.
        Keeps the \begin{multline*}...\end{multline*} inside $$ delimiters.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with converted multline environments.
        """
        def replacer(match):
            # Keep the full match including \begin{multline*}...\end{multline*}
            return f"$$\n{match.group(0)}\n$$"
        
        return self.multline_pattern.sub(replacer, content)
    
    def clean_math_for_katex(self, content: str) -> str:
        """Cleans and converts all LaTeX math expressions to MDX/KaTeX format.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with all math expressions converted.
        """
        replacements = {
            r'\\mbox\{': r'\\text{',
            r'\\;': r'\\,',
        }
        
        for old, new in replacements.items():
            content = re.sub(old, new, content)
        return content
    
    def handle_nested_brackets(self, content: str) -> str:
        """Handles nested brackets in LaTeX math expressions.

        Args:
            content (str): Content to be processed.
        Returns:
            str: Content with handled nested brackets.
        """
        # Hopefully, KaTeX can handle nested brackets correctly.
        # If specific handling is needed, implement it here.
        return content
    
    def convert(self, content: str) -> str:
        """Main method to convert LaTeX math expressions to MDX/KaTeX format.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Fully converted content.
        """
        content, protected_blocks = self.protect_existing_math(content)
        
        content = self.convert_align_environment(content)
        content = self.convert_gather_environment(content)
        content = self.convert_multline_environment(content)
        content = self.convert_equation_environment(content)

        content = self.convert_display_math(content)
        content = self.convert_inline_math(content)
                
        content = self.clean_math_for_katex(content)
        content = self.handle_nested_brackets(content)
        
        content = self.restore_protected_math(content, protected_blocks)
        
        return content
    
def convert_math(content: str) -> str:
    """Convenience function to convert LaTeX math expressions to MDX/KaTeX format.

    Args:
        content (str): Content to be processed.

    Returns:
        str: Fully converted content.
    """
    converter = MathConverter()
    return converter.convert(content)

