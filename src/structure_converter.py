r"""
Module for converting and protecting estructures in LaTeX to MDX/KaTeX format.

Changes the \section, \subsection, \subsubsection, \section*, \subsection*, \subsubsection* commands, 
\textbf, \textit, \emph, \underline, and \texttt text formatting commands,
the lists and enumerations and the images and urls to be compatible with MDX/KaTeX.
"""
import re
from typing import List, Tuple
from math_converter import MathConverter

class StructureConverter:
    """
    A class to convert and protect LaTeX structures in content for MDX/KaTeX formatting.
    """

    def __init__(self):
        """Initialize the StructureConverter."""
        self.section_pattern = re.compile(r'\\section\*?\{([^}]+)\}')
        self.subsection_pattern = re.compile(r'\\subsection\*?\{([^}]+)\}')
        self.subsubsection_pattern = re.compile(r'\\subsubsection\*?\{([^}]+)\}')
        
        self.textbf_pattern = re.compile(r'\\textbf\{([^}]+)\}')
        self.textit_pattern = re.compile(r'\\textit\{([^}]+)\}')
        self.emph_pattern = re.compile(r'\\emph\{([^}]+)\}')
        self.underline_pattern = re.compile(r'\\underline\{([^}]+)\}')
        
        self.itemize_pattern = re.compile(r'\\begin\{itemize\}(.*?)\\end\{itemize\}', re.DOTALL)
        self.enumerate_pattern = re.compile(r'\\begin\{enumerate\}(.*?)\\end\{enumerate\}', re.DOTALL)
        
        # Patrones para entornos que deben eliminarse o convertirse
        self.center_pattern = re.compile(r'\\begin\{center\}(.*?)\\end\{center\}', re.DOTALL)
        self.tabular_pattern = re.compile(r'\\begin\{tabular\}(\{[^}]*\})(.*?)\\end\{tabular\}', re.DOTALL)
        
        # Comandos LaTeX individuales que deben eliminarse
        self.noindent_pattern = re.compile(r'\\noindent\s*')
        self.newpage_pattern = re.compile(r'\\newpage\s*')
        self.maketitle_pattern = re.compile(r'\\maketitle\s*')
        self.tableofcontents_pattern = re.compile(r'\\tableofcontents\s*')
        self.hypersetup_pattern = re.compile(r'\\hypersetup\{[^}]*\}\s*')
        self.nobgthispage_pattern = re.compile(r'\\NoBgThispage\s*', re.IGNORECASE)
        
        self.includegraphics_pattern = re.compile(r'\\includegraphics(?:\[.*?\])?\{([^}]+)\}')
        self.url_pattern = re.compile(r'\\url\{([^}]+)\}')
        self.href_pattern = re.compile(r'\\href\{([^}]+)\}\{([^}]+)\}')
        
        self.math_converter = MathConverter()
    
    def process_texorpdfstring(self, content: str) -> str:
        """Process \\texorpdfstring commands extracting the first argument.
        
        \\texorpdfstring{LaTeX version}{Plain text version}
        We keep the LaTeX version (first argument) and discard the plain text.
        
        Args:
            content (str): Content with potential \\texorpdfstring commands.
        
        Returns:
            str: Content with \\texorpdfstring resolved to first argument.
        """
        # Pattern to match \texorpdfstring{arg1}{arg2}
        # We need to handle nested braces in arg1
        def replace_texorpdfstring(match):
            # Extract the first argument (with LaTeX formatting)
            return match.group(1)
        
        # Match \texorpdfstring{...}{...} handling nested braces
        pattern = r'\\texorpdfstring\{((?:[^{}]|\{[^}]*\})*)\}\{(?:[^{}]|\{[^}]*\})*\}'
        content = re.sub(pattern, replace_texorpdfstring, content)
        
        return content
    
    def convert_sections(self, content: str) -> str:
        """Convert LaTeX sectioning commands to MDX/KaTeX format.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with converted sections.
        """
        content = self.section_pattern.sub(r'## \1', content)
        content = self.subsection_pattern.sub(r'### \1', content)
        content = self.subsubsection_pattern.sub(r'#### \1', content)
        return content
    
    def convert_text_formatting(self, content: str) -> str:
        """Convert LaTeX text formatting commands to MDX/KaTeX format.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with converted text formatting.
        """
        content = self.textbf_pattern.sub(r'**\1**', content)
        content = self.textit_pattern.sub(r'*\1*', content)
        content = self.emph_pattern.sub(r'*\1*', content)
        content = self.underline_pattern.sub(r'<u>\1</u>', content)
        return content
    
    def convert_lists(self, content: str) -> str:
        """Convert LaTeX lists to MDX/KaTeX format.
        Handles nested lists by processing innermost lists first.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with converted lists.
        """
        def convert_itemize(match):
            # Capturar items completos con sus etiquetas personalizadas
            items_text = match.group(1)
            # Buscar \item con o sin etiqueta: \item[label] texto o \item texto
            # Usar DOTALL para capturar múltiples líneas incluidos bloques matemáticos
            item_pattern = r'\\item(?:\[([^\]]*)\])?\s*(.+?)(?=\\item(?:\[[^\]]*\])?|$)'
            items = re.findall(item_pattern, items_text, re.DOTALL)
            
            result = []
            for label, text in items:
                text = text.strip()
                if not text:
                    continue
                if label:
                    # Si hay etiqueta personalizada, ponerla en negrita al inicio
                    result.append(f'- **{label}** {text}')
                else:
                    result.append(f'- {text}')
            
            return '\n' + '\n'.join(result) + '\n' if result else ''
        
        def convert_enumerate(match):
            # Capturar items completos con sus etiquetas personalizadas
            items_text = match.group(1)
            # Buscar \item con o sin etiqueta: \item[label] texto o \item texto
            # Usar DOTALL para capturar múltiples líneas incluidos bloques matemáticos
            item_pattern = r'\\item(?:\[([^\]]*)\])?\s*(.+?)(?=\\item(?:\[[^\]]*\])?|$)'
            items = re.findall(item_pattern, items_text, re.DOTALL)
            
            result = []
            counter = 1
            for label, text in items:
                text = text.strip()
                if not text:
                    continue
                if label:
                    # Si hay etiqueta personalizada, usarla en lugar del número
                    result.append(f'- **{label}** {text}')
                else:
                    result.append(f'{counter}. {text}')
                    counter += 1
            
            return '\n' + '\n'.join(result) + '\n' if result else ''
        
        # Process nested lists iteratively from innermost to outermost
        # Keep replacing until no more list environments are found
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        while iteration < max_iterations:
            old_content = content
            content = self.itemize_pattern.sub(convert_itemize, content)
            content = self.enumerate_pattern.sub(convert_enumerate, content)
            if content == old_content:
                break  # No more changes
            iteration += 1
        
        # Remove any remaining \end{itemize} and \end{enumerate} tags
        content = re.sub(r'\\end\{itemize\}', '', content)
        content = re.sub(r'\\end\{enumerate\}', '', content)
        # Also remove any remaining \begin tags that weren't matched
        content = re.sub(r'\\begin\{itemize\}', '', content)
        content = re.sub(r'\\begin\{enumerate\}', '', content)
        return content
    
    def convert_images_and_urls(self, content: str) -> str:
        """Convert LaTeX images and URLs to MDX/KaTeX format.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with converted images and URLs.
        """
        content = self.includegraphics_pattern.sub(r'![](\1)', content)
        content = self.url_pattern.sub(r'[\1](\1)', content)
        content = self.href_pattern.sub(r'[\2](\1)', content)
        return content
    
    def convert_tabular_to_array(self, content: str) -> str:
        """Convert tabular environments to array in display math.
        Must be called BEFORE math protection to properly handle inline math inside tables.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with tabular converted to array in display math.
        """
        def handle_tabular(match):
            column_spec = match.group(1)  # e.g., {rcl} or {c|cccccccc}
            table_content = match.group(2)
            # Remove inline math delimiters from content since it will be in a display math block
            # Remove $...$ delimiters
            table_content = re.sub(r'\$', '', table_content)
            # Remove \(...\) delimiters
            table_content = re.sub(r'\\[\(\)]', '', table_content)
            # Convert tabular to array (which works in KaTeX)
            return f'\n$$\n\\begin{{array}}{column_spec}{table_content}\\end{{array}}\n$$\n'
        
        # Also handle center+tabular together
        center_tabular_pattern = re.compile(
            r'\\begin\{center\}\s*\\begin\{tabular\}(\{[^}]*\})(.*?)\\end\{tabular\}\s*\\end\{center\}',
            re.DOTALL
        )
        content = center_tabular_pattern.sub(handle_tabular, content)
        
        # Handle standalone tabular
        content = self.tabular_pattern.sub(handle_tabular, content)
        
        return content
    
    def remove_latex_commands(self, content: str) -> str:
        """Remove common LaTeX commands that are not needed in MDX.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content without unnecessary LaTeX commands.
        """
        content = self.noindent_pattern.sub('', content)
        content = self.newpage_pattern.sub('\n\n', content)
        content = self.maketitle_pattern.sub('', content)
        content = self.tableofcontents_pattern.sub('', content)
        content = self.hypersetup_pattern.sub('', content)
        content = self.nobgthispage_pattern.sub('', content)
        
        # Eliminar cualquier \begin{center} y \end{center} que quede sin convertir
        content = re.sub(r'\\begin\{center\}', '', content)
        content = re.sub(r'\\end\{center\}', '', content)
        
        return content
    
    def convert_environments(self, content: str) -> str:
        """Convert or remove LaTeX environments that shouldn't appear in MDX.
        
        Note: tabular conversion is done earlier in the pipeline (before math protection).
        This only handles remaining center tags.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with environments converted.
        """
        # Convert \begin{center}...\end{center} - just unwrap the content
        def unwrap_center(match):
            inner = match.group(1).strip()
            return f'\n{inner}\n'
        
        content = self.center_pattern.sub(unwrap_center, content)
        
        return content
    
    def delete_vspace_commands(self, content: str) -> str:
        """Delete LaTeX \vspace commands from content.

        Args:
            content (str): Content to be processed.
        Returns:
            str: Content without \vspace commands.
        """
        vspace_pattern = re.compile(r'\\vspace\{[^}]+\}')
        return vspace_pattern.sub('', content)
    
    
    def convert(self, content: str) -> str:
        """Convert all LaTeX structures to MDX/KaTeX format.
        It protects math expressions during the conversion.

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with all structures converted.
        """
        protected_content, protected_blocks = self.math_converter.protect_existing_math(content)
        
        # Procesar \texorpdfstring antes de convertir secciones
        protected_content = self.process_texorpdfstring(protected_content)
        
        # Convertir entornos LaTeX primero (antes de procesar listas para evitar conflictos)
        protected_content = self.convert_environments(protected_content)
        
        protected_content = self.convert_sections(protected_content)
        protected_content = self.convert_text_formatting(protected_content)
        protected_content = self.convert_lists(protected_content)
        protected_content = self.convert_images_and_urls(protected_content)
        
        # Eliminar comandos LaTeX sobrantes al final
        protected_content = self.remove_latex_commands(protected_content)
        
        converted_content = self.math_converter.restore_protected_math(protected_content, protected_blocks)
        
        return converted_content
           