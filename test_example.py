"""
Script simple para testear el parser con un archivo LaTeX de ejemplo
"""
import sys
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parser import TexToMdxParser

def main():
    # Leer el archivo LaTeX
    input_file = Path(__file__).parent / 'ejemplo.tex'
    output_file = Path(__file__).parent / 'ejemplo.mdx'
    
    if not input_file.exists():
        print(f"Error: El archivo {input_file} no existe")
        print("Por favor, crea un archivo ejemplo.tex con contenido LaTeX")
        return
    
    print(f"Leyendo archivo: {input_file}")
    latex_content = input_file.read_text(encoding='utf-8')
    
    print("Procesando LaTeX a MDX...")
    parser = TexToMdxParser()
    mdx_output = parser.parse(latex_content)
    
    print(f"Guardando resultado en: {output_file}")
    output_file.write_text(mdx_output, encoding='utf-8')
    
    print("Conversion completada!")
    print("\nResultado (primeras 50 lineas):")
    print("-" * 50)
    lines = mdx_output.split('\n')
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3}: {line}")
    print("-" * 50)
    print(f"Total de lineas: {len(lines)}")

if __name__ == "__main__":
    main()
