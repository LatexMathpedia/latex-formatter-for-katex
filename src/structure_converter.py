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

        Args:
            content (str): Content to be processed.

        Returns:
            str: Content with converted lists.
        """
        def convert_itemize(match):
            # Capturar items completos, no solo la primera línea
            items_text = match.group(1)
            # Manejar \item con etiqueta personalizada: \item[label]
            items = re.split(r'\\item(?:\[[^\]]*\])?\s*', items_text)
            # Filtrar items vacíos
            items = [item.strip() for item in items if item.strip()]
            return '\n- ' + '\n- '.join(items) + '\n'
        
        def convert_enumerate(match):
            # Capturar items completos, no solo la primera línea
            items_text = match.group(1)
            # Manejar \item con etiqueta personalizada: \item[label]
            items = re.split(r'\\item(?:\[[^\]]*\])?\s*', items_text)
            # Filtrar items vacíos
            items = [item.strip() for item in items if item.strip()]
            return '\n' + '\n'.join(f'{i+1}. {item}' for i, item in enumerate(items)) + '\n'
        
        content = self.itemize_pattern.sub(convert_itemize, content)
        content = self.enumerate_pattern.sub(convert_enumerate, content)
        
        # Remove the \end{itemize} and \end{enumerate} tags if any remain
        content = re.sub(r'\\end\{itemize\}', '', content)
        content = re.sub(r'\\end\{enumerate\}', '', content)
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
        
        # Eliminar cualquier \begin{...} y \end{...} que quede sin convertir
        # (excepto los que deban estar en bloques matemáticos)
        content = re.sub(r'\\begin\{(itemize|enumerate|center)\}', '', content)
        content = re.sub(r'\\end\{(itemize|enumerate|center)\}', '', content)
        
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
           