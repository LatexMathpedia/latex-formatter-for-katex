""".
Module forparsing a full LaTeX document into a MDX-compatible format.
"""
import re
import unicodedata
from structure_converter import StructureConverter
from math_converter import MathConverter
from tikz_converter import TikzConverter
from box_converter import BoxConverter

class TexToMdxParser:
    def __init__(self):
        self.math_converter = MathConverter()
        self.structure_converter = StructureConverter()
        self.tikz_converter = None  # Se inicializará después de extraer el título
        self.box_converter = BoxConverter()
        
    def parse(self, latex_content: str) -> str:
        """Pipeline completo de conversión."""
        content = latex_content
        
        # 1. Extraer metadatos (título, autor, etc.)
        metadata = self.extract_metadata(content)
        
        # Crear slug del título para prefijo de imágenes
        title_slug = self._create_slug(metadata.get('title', 'documento'))
        
        # Inicializar TikzConverter con el prefijo basado en el título
        self.tikz_converter = TikzConverter(filename_prefix=title_slug)
        
        # 2. Limpiar preámbulo LaTeX
        content = self.remove_preamble(content)
        
        # 3. Eliminar comandos \vspace (antes de procesar matemáticas)
        content = self.remove_vspace_commands(content)
        
        # 3.4. Eliminar comandos de ecuaciones incompatibles (antes de proteger matemáticas)
        content = self.remove_equation_commands(content)
        
        # 3.5. Convertir tabular a array ANTES de proteger matemáticas
        content = self.structure_converter.convert_tabular_to_array(content)
        
        # 4. Convertir TikZ (primero porque genera archivos)
        content, _ = self.tikz_converter.convert_content(content)
        
        # 5. Convertir cajas personalizadas
        content = self.box_converter.convert(content)
        
        # 6. Convertir matemáticas
        content = self.math_converter.convert(content)
        
        # 7. Convertir estructura
        content = self.structure_converter.convert(content)
        
        # 8. Post-procesamiento y limpieza
        content = self.postprocess(content)
        
        # 9. Añadir frontmatter
        mdx_output = self.generate_frontmatter(metadata) + content
        
        return mdx_output
    
    def remove_vspace_commands(self, content: str) -> str:
        """Eliminar comandos \\vspace y \\footnote del contenido LaTeX.
        
        Args:
            content (str): Contenido con posibles comandos \\vspace y \\footnote.
        
        Returns:
            str: Contenido sin comandos \\vspace ni \\footnote.
        """
        # Eliminar \vspace{...} y \vspace*{...}
        content = re.sub(r'\\vspace\*?\{[^}]+\}', '', content)
        # Eliminar \footnote{...}
        content = re.sub(r'\\footnote\{[^}]+\}', '', content)
        # Eliminar \addcontentsline{...}{...}{...}
        content = re.sub(r'\\addcontentsline\{[^}]+\}\{[^}]+\}\{[^}]+\}', '', content)
        # Eliminar \newpage
        content = re.sub(r'\\newpage', '', content)
        return content
    
    def remove_equation_commands(self, content: str) -> str:
        """Eliminar comandos de ecuaciones incompatibles con KaTeX.
        
        Args:
            content (str): Contenido con posibles comandos \\tag, \\label y \\eqref.
        
        Returns:
            str: Contenido sin comandos \\tag, \\label ni \\eqref.
        """
        # Eliminar \tag{...}
        content = re.sub(r'\\tag\{[^}]*\}', '', content)
        # Eliminar \label{...}
        content = re.sub(r'\\label\{[^}]*\}', '', content)
        # Eliminar \eqref{...}
        content = re.sub(r'\\eqref\{[^}]*\}', '', content)
        return content
    
    def _create_slug(self, text: str) -> str:
        """Convierte un texto en un slug válido para nombres de archivo.
        
        Args:
            text: Texto a convertir (por ejemplo, 'TEMA 1: Preliminares')
            
        Returns:
            str: Slug válido (por ejemplo, 'tema-1-preliminares')
        """
        # Normalizar unicode y convertir a minúsculas
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        text = text.lower()
        
        # Reemplazar espacios y caracteres no alfanuméricos con guiones
        text = re.sub(r'[^a-z0-9]+', '-', text)
        
        # Eliminar guiones al inicio y final
        text = text.strip('-')
        
        # Limitar longitud para evitar nombres muy largos
        if len(text) > 50:
            text = text[:50].rsplit('-', 1)[0]
        
        return text
    
    def extract_metadata(self, content: str) -> dict:
        """Extract metadata from LaTeX content."""
        metadata = {}
        # Match \title{...} handling nested braces
        title_match = re.search(r'\\title\{((?:[^{}]|\{[^}]*\})*)\}', content)
        author_match = re.search(r'\\author\{([^}]+)\}', content)
        date_match = re.search(r'\\date\{([^}]+)\}', content)
        
        if title_match:
            # Title may be like: \textbf{Tema 1:} Introducción -> we want Tema 1: Introducción
            text_bold_pattern = re.compile(r'\\textbf\{([^}]+)\}')
            full_title = text_bold_pattern.sub(r'\1', title_match.group(1))
            metadata['title'] = full_title.strip()
        if author_match:
            metadata['author'] = author_match.group(1).strip()
        if date_match:
            metadata['date'] = date_match.group(1).strip()
        
        return metadata
    
    def remove_preamble(self, content: str) -> str:
        """Remove LaTeX preamble from content."""
        document_start = re.search(r'\\begin\{document\}', content)
        document_end = re.search(r'\\end\{document\}', content)
        
        if document_start and document_end:
            content = content[document_start.end():document_end.start()]
        
        return content.strip()
    
    def postprocess(self, content: str) -> str:
        """Final cleanup of the content."""
        # Remove leading whitespace from lines (normalize indentation)
        # This prevents MDX from interpreting indented lines as code blocks
        lines = content.split('\n')
        processed_lines = []
        for line in lines:
            # Keep empty lines as-is
            if line.strip() == '':
                processed_lines.append('')
            # Remove leading spaces but preserve list markers and other structure
            else:
                processed_lines.append(line.lstrip())
        
        content = '\n'.join(processed_lines)
        
        # Remove excessive blank lines
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        return content.strip()
    
    def generate_frontmatter(self, metadata: dict) -> str:
        """Generate MDX frontmatter from metadata."""
        frontmatter = '---\n'
        for key, value in metadata.items():
            frontmatter += f'{key}: "{value}"\n'
        frontmatter += '---\n\n'
        return frontmatter