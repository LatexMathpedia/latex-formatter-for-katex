"""
tex-to-mdx: Convertidor de archivos LaTeX a MDX para KaTeX
"""

from .math_converter import MathConverter, convert_math

__version__ = "0.1.0"
__all__ = ["MathConverter", "convert_math"]