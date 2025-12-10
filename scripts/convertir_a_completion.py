#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para convertir subset QA a formato completion para Logit Lens
Transforma: "¿Cuál es X de Y?" -> "El X de Y es"
"""

import json
import re
from typing import Dict, List


class QAToCompletionConverter:
    """Conversor de formato QA a formato Completion"""
    
    def __init__(self):
        # Patrones de conversión de preguntas a frases incompletas
        self.patterns = [
            # ¿Cuál es el/la X de Y? -> El/La X de Y es
            (r'¿Cuál es el (.+) de (.+)\?', r'El \1 de \2 es'),
            (r'¿Cuál es la (.+) de (.+)\?', r'La \1 de \2 es'),
            (r'¿Cuál es un (.+) de (.+)\?', r'Un \1 de \2 es'),
            (r'¿Cuál es una (.+) de (.+)\?', r'Una \1 de \2 es'),
            
            # ¿Cuál es X? -> El X es / X es
            (r'¿Cuál es (.+)\?', r'\1 es'),
            
            # Casos especiales comunes
            (r'¿Cuál es el país de (.+)\?', r'El país de \1 es'),
            (r'¿Cuál es la ciudad de (.+)\?', r'La ciudad de \1 es'),
            (r'¿Cuál es el idioma de (.+)\?', r'El idioma de \1 es'),
            (r'¿Cuál es el autor de (.+)\?', r'El autor de \1 es'),
            (r'¿Cuál es el director de (.+)\?', r'El director de \1 es'),
            (r'¿Cuál es el creador de (.+)\?', r'El creador de \1 es'),
        ]
    
    def question_to_completion(self, pregunta: str) -> str:
        """
        Convierte una pregunta a formato completion
        
        Args:
            pregunta: Pregunta en formato "¿Cuál es X de Y?"
            
        Returns:
            Frase incompleta "El X de Y es"
        """
        # Aplicar patrones en orden
        for pattern, replacement in self.patterns:
            match = re.match(pattern, pregunta)
            if match:
                completion = re.sub(pattern, replacement, pregunta)
                # Limpiar espacios dobles
                completion = re.sub(r'\s+', ' ', completion).strip()
                return completion
        
        # Si no hay match, intentar conversión genérica
        # Quitar signos de interrogación y ajustar
        if pregunta.startswith('¿'):
            cleaned = pregunta.replace('¿', '').replace('?', '').strip()
            # Si empieza con "Cuál es", reemplazar por estructura afirmativa
            if cleaned.lower().startswith('cuál es'):
                cleaned = cleaned[8:].strip()  # Quitar "Cuál es "
                return cleaned + ' es'
            return cleaned + ' es'
        
        return pregunta
    
    def convert_subset(self, input_file: str, output_file: str):
        """
        Convierte subset de QA a formato completion
        
        Args:
            input_file: Archivo JSON de entrada (formato QA)
            output_file: Archivo JSON de salida (formato completion)
        """
        print(f"\n{'='*80}")
        print("CONVERSIÓN: QA → COMPLETION (Logit Lens)")
        print(f"{'='*80}\n")
        
        # Leer subset QA
        print(f"📖 Leyendo {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convertir a formato completion
        completion_data = []
        total_items = 0
        
        for category in ['indigenous_peoples', 'dances', 'painters', 'movies', 'landmarks']:
            items = data.get(category, [])
            
            for item in items:
                entidad = item.get('entidad', '')
                preguntas = item.get('preguntas', [])
                
                for pregunta_obj in preguntas:
                    pregunta = pregunta_obj.get('pregunta', '')
                    respuesta = pregunta_obj.get('respuesta_correcta', '')
                    
                    # Convertir pregunta a completion
                    input_text = self.question_to_completion(pregunta)
                    
                    # Crear item en formato completion
                    completion_item = {
                        'input_text': input_text,
                        'target': respuesta,
                        'category': category,
                        'entity': entidad,
                        'original_question': pregunta  # Mantener para referencia
                    }
                    
                    completion_data.append(completion_item)
                    total_items += 1
        
        # Guardar en formato completion
        print(f"\n💾 Guardando {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(completion_data, f, ensure_ascii=False, indent=4)
        
        # Mostrar estadísticas
        print(f"\n{'='*80}")
        print("ESTADÍSTICAS DE CONVERSIÓN")
        print(f"{'='*80}\n")
        
        # Contar por categoría
        from collections import Counter
        category_counts = Counter(item['category'] for item in completion_data)
        
        for category in ['indigenous_peoples', 'dances', 'painters', 'movies', 'landmarks']:
            count = category_counts.get(category, 0)
            print(f"{category:25s}: {count:3d} items")
        
        print(f"\n{'='*80}")
        print(f"Total de items convertidos: {total_items}")
        print(f"{'='*80}\n")
        
        # Mostrar ejemplos
        print("EJEMPLOS DE CONVERSIÓN:\n")
        for i, item in enumerate(completion_data[:10], 1):
            print(f"{i}. Categoría: {item['category']}")
            print(f"   Original:  {item['original_question']}")
            print(f"   → Input:   {item['input_text']}")
            print(f"   → Target:  {item['target']}")
            print()
        
        if len(completion_data) > 10:
            print(f"... y {len(completion_data) - 10} items más\n")
        
        print(f"✅ Archivo guardado: {output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convertir subset QA a formato completion para Logit Lens'
    )
    parser.add_argument(
        '--input',
        default='subset_h2_limpio.json',
        help='Archivo QA de entrada (default: subset_h2_limpio.json)'
    )
    parser.add_argument(
        '--output',
        default='subset_h2_completion.json',
        help='Archivo completion de salida (default: subset_h2_completion.json)'
    )
    
    args = parser.parse_args()
    
    converter = QAToCompletionConverter()
    converter.convert_subset(args.input, args.output)
    
    print(f"\n{'='*80}")
    print("✨ CONVERSIÓN COMPLETADA ✨")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
