"""
Module for detecting and converting TikZ pictures and PGFPlots in LaTeX 
to svg format for MDX/KaTeX.

Creates a temporal LaTeX file, compiles it with a subprocess and pdflatex
Uses dvisvgm (preferred), pdf2svg (Linux/Mac) or inkscape as fallback.
Saves the svg and references it in the MDX content.
"""
import re
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple, Optional

class TikzConverter:
    def __init__(self, output_dir: str = "./images", converter: Optional[str] = None, filename_prefix: str = ""):
        """Initialize the TikZConverter with regex patterns for TikZ and PGFPlots.
        
        Args:
            output_dir: Directory where SVG files will be saved
            converter: Force a specific converter ('dvisvgm', 'pdf2svg', 'inkscape'). 
                      If None, will auto-detect the best available option.
            filename_prefix: Prefix to add to generated SVG filenames (e.g., 'tema-1-preliminares')
        """
        self.tikz_pattern = re.compile(
            r'\\begin\{tikzpicture\}(.*?)\\end\{tikzpicture\}',
            re.DOTALL
        )
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.image_counter = 0
        self.filename_prefix = filename_prefix
        
        # Detectar el mejor conversor disponible
        self.converter = converter or self._detect_converter()
        
        if self.converter is None:
            raise RuntimeError(
                "No se encontró ningún conversor PDF/DVI a SVG instalado.\n"
                "Por favor instala una de estas opciones:\n"
                "  - dvisvgm (recomendado, incluido en MiKTeX y TeX Live)\n"
                "  - pdf2svg (Linux/Mac: sudo apt install pdf2svg)\n"
                "  - inkscape (https://inkscape.org/)\n"
            )
        
        print(f"Usando conversor: {self.converter}")
    
    def _detect_converter(self) -> Optional[str]:
        """Detecta qué conversor está disponible en el sistema.
        
        Returns:
            Nombre del conversor disponible o None si ninguno está disponible.
        """
        # Orden de preferencia: dvisvgm > pdf2svg > inkscape
        converters = ['dvisvgm', 'pdf2svg', 'inkscape']
        
        for converter in converters:
            if shutil.which(converter):
                return converter
        
        return None
    
    def _check_pdflatex(self) -> bool:
        """Verifica si pdflatex está disponible."""
        return shutil.which('pdflatex') is not None
    
    def _check_latex(self) -> bool:
        """Verifica si latex está disponible."""
        return shutil.which('latex') is not None
        
    def extract_tikz_blocks(self, content: str) -> list:
        """Extracts TikZ blocks from the content.

        Args:
            content (str): Content to be processed.
        Returns:
            list: List of TikZ blocks.
        """
        return self.tikz_pattern.findall(content)
        
    def convert_tikz_to_svg(self, tikz_code: str) -> str:
        """Converts a TikZ code block to SVG format.

        Args:
            tikz_code (str): TikZ code to be converted.
        Returns:
            str: Path to the generated SVG file.
        Raises:
            RuntimeError: If compilation or conversion fails.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Nombre del archivo SVG de salida
            if self.filename_prefix:
                svg_filename = f"{self.filename_prefix}_tikz_{self.image_counter}.svg"
            else:
                svg_filename = f"tikz_{self.image_counter}.svg"
            svg_path = self.output_dir / svg_filename
            self.image_counter += 1
            
            try:
                if self.converter == 'dvisvgm':
                    # Método preferido: latex + dvisvgm
                    self._convert_with_dvisvgm(tikz_code, tmpdir_path, svg_path)
                elif self.converter == 'pdf2svg':
                    # Linux/Mac: pdflatex + pdf2svg
                    self._convert_with_pdf2svg(tikz_code, tmpdir_path, svg_path)
                elif self.converter == 'inkscape':
                    # Fallback: pdflatex + inkscape
                    self._convert_with_inkscape(tikz_code, tmpdir_path, svg_path)
                else:
                    raise RuntimeError(f"Conversor no soportado: {self.converter}")
                
                return svg_filename
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Error al compilar/convertir TikZ: {e}\n"
                if e.stderr:
                    error_msg += f"stderr: {e.stderr.decode('utf-8', errors='ignore')}\n"
                raise RuntimeError(error_msg)
    
    def _convert_with_dvisvgm(self, tikz_code: str, tmpdir: Path, svg_path: Path):
        """Convierte usando latex + dvisvgm (método más robusto).
        
        Este método funciona en Windows, Linux y Mac si tienes TeX Live o MiKTeX.
        """
        tex_file = tmpdir / "tikz.tex"
        dvi_file = tmpdir / "tikz.dvi"
        
        # Crear documento LaTeX (para latex, no pdflatex)
        latex_doc = self.create_standalone_document(tikz_code, for_dvi=True)
        tex_file.write_text(latex_doc, encoding='utf-8')
        
        # Compilar con latex (genera DVI)
        result = subprocess.run(
            ['latex', '-interaction=nonstopmode', '-output-directory', str(tmpdir), str(tex_file)],
            capture_output=True,
            cwd=str(tmpdir)
        )
        
        if result.returncode != 0 or not dvi_file.exists():
            raise subprocess.CalledProcessError(
                result.returncode, 
                result.args, 
                result.stdout, 
                result.stderr
            )
        
        # Convertir DVI a SVG con dvisvgm - usar ruta absoluta para el output
        result = subprocess.run(
            ['dvisvgm', '--no-fonts', '--exact', str(dvi_file), '-o', str(svg_path.resolve())],
            capture_output=True,
            cwd=str(tmpdir),
            check=True
        )
    
    def _convert_with_pdf2svg(self, tikz_code: str, tmpdir: Path, svg_path: Path):
        """Convierte usando pdflatex + pdf2svg (Linux/Mac)."""
        tex_file = tmpdir / "tikz.tex"
        pdf_file = tmpdir / "tikz.pdf"
        
        # Crear documento LaTeX
        latex_doc = self.create_standalone_document(tikz_code, for_dvi=False)
        tex_file.write_text(latex_doc, encoding='utf-8')
        
        # Compilar con pdflatex
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', str(tmpdir), str(tex_file)],
            capture_output=True,
            cwd=str(tmpdir)
        )
        
        if result.returncode != 0 or not pdf_file.exists():
            raise subprocess.CalledProcessError(
                result.returncode, 
                result.args, 
                result.stdout, 
                result.stderr
            )
        
        # Convertir PDF a SVG con pdf2svg - usar ruta absoluta
        subprocess.run(
            ['pdf2svg', str(pdf_file), str(svg_path.resolve())],
            capture_output=True,
            check=True
        )
    
    def _convert_with_inkscape(self, tikz_code: str, tmpdir: Path, svg_path: Path):
        """Convierte usando pdflatex + inkscape (fallback multiplataforma)."""
        tex_file = tmpdir / "tikz.tex"
        pdf_file = tmpdir / "tikz.pdf"
        
        # Crear documento LaTeX
        latex_doc = self.create_standalone_document(tikz_code, for_dvi=False)
        tex_file.write_text(latex_doc, encoding='utf-8')
        
        # Compilar con pdflatex
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', str(tmpdir), str(tex_file)],
            capture_output=True,
            cwd=str(tmpdir)
        )
        
        if result.returncode != 0 or not pdf_file.exists():
            raise subprocess.CalledProcessError(
                result.returncode, 
                result.args, 
                result.stdout, 
                result.stderr
            )
        
        # Convertir PDF a SVG con inkscape - usar ruta absoluta
        subprocess.run(
            ['inkscape', str(pdf_file), '--export-plain-svg', str(svg_path.resolve())],
            capture_output=True,
            check=True
        )
        
    def create_standalone_document(self, tikz_code: str, for_dvi: bool = False) -> str:
        """Creates a standalone LaTeX document with the given TikZ code.

        Args:
            tikz_code (str): TikZ code to be included in the document.
            for_dvi (bool): If True, creates a document compatible with latex (not pdflatex).
        Returns:
            str: Complete LaTeX document as a string.
        """
        # Para DVI (latex), no usar el paquete fontenc con T1 que puede causar problemas
        if for_dvi:
            return f"""\\documentclass{{standalone}}
\\usepackage{{tikz}}
\\usepackage{{pgfplots}}
\\pgfplotsset{{compat=1.18}}
\\usetikzlibrary{{arrows.meta, shapes, positioning}}
\\begin{{document}}
\\begin{{tikzpicture}}
{tikz_code}
\\end{{tikzpicture}}
\\end{{document}}
"""
        else:
            # Para PDF (pdflatex)
            return f"""\\documentclass{{standalone}}
\\usepackage{{tikz}}
\\usepackage{{pgfplots}}
\\pgfplotsset{{compat=1.18}}
\\usetikzlibrary{{arrows.meta, shapes, positioning}}
\\begin{{document}}
\\begin{{tikzpicture}}
{tikz_code}
\\end{{tikzpicture}}
\\end{{document}}
"""

    def convert_content(self, content: str) -> Tuple[str, List[str]]:
        """Converts all TikZ blocks in the content to SVG and updates the content.

        Args:
            content (str): Content to be processed.
        Returns:
            Tuple[str, List[str]]: Updated content and list of generated SVG filenames.
        """
        tikz_blocks = self.extract_tikz_blocks(content)
        svg_filenames = []
        
        for tikz_code in tikz_blocks:
            try:
                print(f"Convirtiendo gráfico TikZ {len(svg_filenames) + 1}...")
                svg_filename = self.convert_tikz_to_svg(tikz_code)
                svg_filenames.append(svg_filename)
                
                # Reemplazar el bloque TikZ con la referencia a la imagen
                tikz_block = f"\\begin{{tikzpicture}}{tikz_code}\\end{{tikzpicture}}"
                # Usar ruta absoluta /blogs/images/
                image_path = f"/blogs/images/{svg_filename}"
                image_markdown = f"\n![TikZ Graph]({image_path})\n"
                
                content = content.replace(tikz_block, image_markdown)
                print(f"  OK: Guardado como {svg_filename}")
                
            except Exception as e:
                print(f"  ADVERTENCIA: Error al convertir gráfico: {e}")
                print(f"  -> El bloque TikZ se mantendrá en el output")
                # No reemplazar el bloque si falla la conversión
        
        return content, svg_filenames
    
    def process(self, content: str) -> Tuple[str, List[str]]:
        """Processes the content to convert TikZ blocks to SVG.

        Args:
            content (str): Content to be processed.
        Returns:
            Tuple[str, List[str]]: Updated content and list of generated SVG filenames.
        """
        return self.convert_content(content)


# Ejemplo de uso y testing
if __name__ == "__main__":
    # Test simple
    test_tikz = r"""
\documentclass{article}
\usepackage{tikz}
\begin{document}

Aquí hay un gráfico:

\begin{tikzpicture}
  \draw[->] (0,0) -- (3,0) node[right] {$x$};
  \draw[->] (0,0) -- (0,3) node[above] {$y$};
  \draw[domain=0:2.5, smooth, variable=\x, blue, thick] plot ({\x}, {\x*\x/2});
\end{tikzpicture}

Y continúa el texto.
\end{document}
"""
    
    print("🧪 Probando TikzConverter...")
    print("=" * 60)
    
    try:
        converter = TikzConverter(output_dir="./test_images")
        result, images = converter.process(test_tikz)
        
        print("\n✅ Conversión exitosa!")
        print(f"Imágenes generadas: {images}")
        print("\nContenido resultante:")
        print(result)
    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Solución para Windows:")
        print("1. Instala MiKTeX: https://miktex.org/download")
        print("2. Durante la instalación, asegúrate de marcar 'Add to PATH'")
        print("3. Reinicia tu terminal/IDE")
        print("4. dvisvgm viene incluido con MiKTeX")