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
        
        # 2.5. Eliminar entornos minipage (antes de procesar el resto)
        content = self.remove_minipage_environments(content)
        
        # 2.6. Convertir lstlisting a bloques de código
        content = self.convert_lstlisting_to_code_blocks(content)
        
        # 3. Eliminar comandos \vspace (antes de procesar matemáticas)
        content = self.remove_vspace_commands(content)
        
        # 3.4. Eliminar comandos de ecuaciones incompatibles (antes de proteger matemáticas)
        content = self.remove_equation_commands(content)
        
        # 3.5. Convertir tabular a array ANTES de proteger matemáticas
        content = self.structure_converter.convert_tabular_to_array(content)
        
        # 4. Convertir TikZ (primero porque genera archivos)
        content, _ = self.tikz_converter.convert_content(content)
        
        # 5. Convertir cajas personalizadas con procesamiento de listas dentro
        def process_box_content(box_content):
            """Process content inside boxes: convert lists"""
            return self.structure_converter.convert_lists(box_content)
        
        content = self.box_converter.convert(content, content_processor=process_box_content)
        
        # 6. Convertir matemáticas
        content = self.math_converter.convert(content)
        
        # 7. Convertir estructura (ahora las listas fuera de cajas)
        content = self.structure_converter.convert(content)
        
        # 8. Post-procesamiento y limpieza
        content = self.postprocess(content)
        
        # 9. Añadir frontmatter
        mdx_output = self.generate_frontmatter(metadata) + content
        
        return mdx_output
    
    def remove_vspace_commands(self, content: str) -> str:
        """Eliminar comandos \\vspace, \\hspace y \\footnote del contenido LaTeX.
        
        Args:
            content (str): Contenido con posibles comandos.
        
        Returns:
            str: Contenido sin estos comandos.
        """
        # Eliminar \vspace{...} y \vspace*{...}
        content = re.sub(r'\\vspace\*?\{[^}]+\}', '', content)
        # Eliminar \hspace{...} y \hspace*{...}
        content = re.sub(r'\\hspace\*?\{[^}]+\}', '', content)
        # Eliminar \footnote{...}
        content = re.sub(r'\\footnote\{[^}]+\}', '', content)
        # Eliminar \addcontentsline{...}{...}{...}
        content = re.sub(r'\\addcontentsline\{[^}]+\}\{[^}]+\}\{[^}]+\}', '', content)
        # Eliminar \newpage
        content = re.sub(r'\\newpage', '', content)
        # Eliminar \leftskip seguido de valor en pt (ej: \leftskip -10pt)
        content = re.sub(r'\\leftskip\s+[+-]?\d+pt', '', content)
        # Eliminar \setlength{\itemsep}{...} y \setlength\itemsep{...} (comandos de espaciado en listas)
        content = re.sub(r'\\setlength\{?\\itemsep\}?\{[^}]+\}', '', content)
        return content
    
    def remove_minipage_environments(self, content: str) -> str:
        """Eliminar entornos minipage del contenido LaTeX.
        
        Args:
            content (str): Contenido con posibles entornos minipage.
        
        Returns:
            str: Contenido sin los tags \\begin{minipage} y \\end{minipage}.
        """
        # Eliminar \begin{minipage}{...}
        content = re.sub(r'\\begin\{minipage\}\{[^}]+\}', '', content)
        # Eliminar \end{minipage}
        content = re.sub(r'\\end\{minipage\}', '', content)
        return content
    
    def convert_lstlisting_to_code_blocks(self, content: str) -> str:
        """Convertir entornos lstlisting de LaTeX a bloques de código MDX.
        
        Args:
            content (str): Contenido con posibles entornos lstlisting.
        
        Returns:
            str: Contenido con bloques de código MDX (```).
        """
        # Convertir \begin{lstlisting}[...] a ``` y \end{lstlisting} a ```
        # El patrón captura cualquier configuración entre [] si existe
        content = re.sub(r'\\begin\{lstlisting\}(?:\[[^\]]*\])?', '```', content)
        content = re.sub(r'\\end\{lstlisting\}', '```', content)
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
        # Convertir \hyperref[label]{texto} a solo texto
        content = re.sub(r'\\hyperref\[[^\]]*\]\{([^}]*)\}', r'\1', content)
        # Reemplazar \underbracket por \underbrace (KaTeX no soporta underbracket)
        content = re.sub(r'\\underbracket', r'\\underbrace', content)
        # Reemplazar \overbracket por \overbrace (KaTeX no soporta overbracket)
        content = re.sub(r'\\overbracket', r'\\overbrace', content)
        # Reemplazar \Lint por \int (comando personalizado no soportado por KaTeX)
        content = re.sub(r'\\Lint', r'\\int', content)
        
        # Convertir \substack{a\\b\\c} a formato simple (KaTeX no lo renderiza correctamente)
        # Usamos una función para manejar llaves anidadas correctamente
        def replace_substack(match):
            inner = match.group(1)
            # Extraer contenido manejando llaves anidadas
            depth = 0
            result = []
            current = []
            i = 0
            while i < len(inner):
                if inner[i] == '{':
                    depth += 1
                    current.append(inner[i])
                elif inner[i] == '}':
                    depth -= 1
                    current.append(inner[i])
                elif depth == 0 and i < len(inner) - 1 and inner[i:i+2] == '\\\\':
                    # Encontramos \\ fuera de llaves anidadas
                    result.append(''.join(current))
                    current = []
                    i += 1  # Saltar el segundo \
                else:
                    current.append(inner[i])
                i += 1
            if current:
                result.append(''.join(current))
            
            # Unir con comas y espacios
            return ', '.join(part.strip() for part in result if part.strip())
        
        # Patrón para capturar \substack{...} manejando llaves anidadas
        pos = 0
        while True:
            match = re.search(r'\\substack\{', content[pos:])
            if not match:
                break
            start = pos + match.start()
            brace_start = pos + match.end() - 1
            
            # Encontrar la llave de cierre correspondiente
            depth = 1
            i = brace_start + 1
            while i < len(content) and depth > 0:
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                i += 1
            
            if depth == 0:
                # Extraer contenido y reemplazar
                inner_content = content[brace_start + 1:i - 1]
                replacement = replace_substack(type('obj', (object,), {'group': lambda self, n: inner_content if n == 1 else None})())
                content = content[:start] + replacement + content[i:]
                pos = start + len(replacement)
            else:
                pos = i
        
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
        # Remove \textcolor{}{} outside of math environments
        content = self.remove_textcolor_outside_math(content)
        
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
    
    def remove_textcolor_outside_math(self, content: str) -> str:
        """Remove \\textcolor{}{} commands outside of math environments.
        
        Args:
            content (str): Content with potential \\textcolor commands.
        
        Returns:
            str: Content with \\textcolor removed outside math, preserving content inside.
        """
        # Protect math environments
        protected_blocks = []
        
        # Protect display math ($$...$$) - must be done first
        def protect_display(match):
            protected_blocks.append(match.group(0))
            return f"__MATH_BLOCK_{len(protected_blocks) - 1}__"
        
        content = re.sub(r'\$\$.*?\$\$', protect_display, content, flags=re.DOTALL)
        
        # Protect inline math ($...$) - use non-greedy match but avoid matching across $$
        def protect_inline(match):
            protected_blocks.append(match.group(0))
            return f"__MATH_BLOCK_{len(protected_blocks) - 1}__"
        
        # Match $ that's not preceded by $ and not followed by $, with content that doesn't contain unescaped $
        content = re.sub(r'(?<!\$)\$(?!\$)([^\$\\]*(?:\\.[^\$\\]*)*)\$(?!\$)', protect_inline, content)
        
        # Now remove \textcolor{color}{text} from non-protected content, keeping only the text
        # Handle nested braces correctly
        pos = 0
        result = []
        pattern = '\\textcolor{'
        
        while True:
            idx = content.find(pattern, pos)
            if idx == -1:
                result.append(content[pos:])
                break
            
            # Add content before \textcolor
            result.append(content[pos:idx])
            
            # Find end of color argument (first {})
            color_start = idx + len(pattern) - 1
            depth = 1
            i = color_start + 1
            while i < len(content) and depth > 0:
                if content[i] == '\\':
                    i += 2
                    continue
                elif content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                i += 1
            
            if depth != 0 or i >= len(content) or content[i] != '{':
                # Malformed, keep original
                result.append(pattern)
                pos = idx + len(pattern)
                continue
            
            # Now find end of text argument (second {})
            text_start = i
            depth = 1
            i = text_start + 1
            while i < len(content) and depth > 0:
                if content[i] == '\\':
                    i += 2
                    continue
                elif content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                i += 1
            
            if depth == 0:
                # Extract text content and discard color
                text_content = content[text_start + 1:i - 1]
                result.append(text_content)
                pos = i
            else:
                # Malformed, keep original
                result.append(pattern)
                pos = idx + len(pattern)
        
        content = ''.join(result)
        
        # Restore protected math
        for i, block in enumerate(protected_blocks):
            content = content.replace(f"__MATH_BLOCK_{i}__", block)
        
        return content
    
    def generate_frontmatter(self, metadata: dict) -> str:
        """Generate MDX frontmatter from metadata."""
        frontmatter = '---\n'
        for key, value in metadata.items():
            frontmatter += f'{key}: "{value}"\n'
        frontmatter += '---\n\n'
        return frontmatter