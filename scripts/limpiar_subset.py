#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de limpieza automática para subset_h2_final.json
Elimina entidades incorrectamente categorizadas
"""

import json
from typing import Dict, List


class SubsetCleaner:
    """Limpiador de subset con reglas específicas por categoría"""
    
    def __init__(self):
        # Lista negra: entidades que NO pertenecen a cada categoría
        self.blacklist = {
            'indigenous_peoples': [
                # Grupos étnicos no-indígenas
                'eslovenos', 'mizrají', 'Armenios en Argentina', 'peruanos',
                'chilenos', 'sino-argentinos', 'argentinos galeses',
                'católicos-irlandeses', 'Nipo-argentinos', 'Nipo-peruano',
                'Tusán', 'Palestinos en Chile', 'Argentinos de ascendencia europea',
                'Amish',
                # Lugares geográficos
                'San Cristóbal', 'Huari', 'Huanca'
            ],
            'painters': [
                # Actores
                'Lautaro Murúa', 'María Izquierdo',
                # Directores de cine
                'Adrián Caetano', 'Rodrigo Plá', 'Juan Pablo Rebella',
                # Escritores/Humoristas
                'Roberto Fontanarrosa', 'Horacio Altuna', 'Juan Carlos Colombres',
                'Ernesto Sabato',
                # Músicos
                'José Ramón Villa Soberón', 'Carlos Orozco',
                # Otros
                'Ignacio Merino'  # Nombre de calle
            ],
            'dances': [
                # Lugares geográficos
                'Habanera', 'Quebradita', 'Picota',
                # Géneros musicales (no danzas)
                'hip hop de Argentina', 'Rock de Chile', 'Rock del Perú',
                'chicha',
                # Ambiguos
                'estilo', 'Tango argentino'  # Es película, no danza
            ],
            'movies': [],
            'landmarks': []
        }
        
        # Palabras clave que DEBEN aparecer en las preguntas para validar
        self.required_keywords = {
            'indigenous_peoples': ['pueblo', 'indigena', 'etnia', 'lengua', 'idioma', 
                                   'ancestral', 'territorio', 'comunidad'],
            'painters': ['pintor', 'artista', 'obra', 'creador', 'museo', 'escultor',
                        'cuadro', 'pintura'],
            'dances': ['danza', 'baile', 'musica', 'genero musical', 'folclore',
                      'ritmo', 'tradicional'],
            'movies': [],
            'landmarks': []
        }
    
    def normalize_text(self, text: str) -> str:
        """Normaliza texto"""
        if not text:
            return ""
        text = text.lower().strip()
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    def should_remove_entity(self, category: str, entity_data: Dict) -> tuple:
        """
        Determina si una entidad debe ser eliminada
        
        Returns:
            (should_remove: bool, reason: str)
        """
        entidad = entity_data.get('entidad', '')
        preguntas = entity_data.get('preguntas', [])
        
        # 1. Verificar lista negra
        if entidad in self.blacklist.get(category, []):
            return True, f"En lista negra de {category}"
        
        # 2. Para painters, verificar que NO sea actor/director
        if category == 'painters':
            texto_completo = ""
            for p in preguntas:
                texto_completo += self.normalize_text(p.get('pregunta', '')) + " "
                texto_completo += self.normalize_text(p.get('respuesta_correcta', '')) + " "
            
            # Si tiene muchas referencias a cine/teatro, probablemente no es pintor
            cine_keywords = ['miembro del reparto', 'cast member', 'guionista', 
                            'director', 'pelicula', 'film']
            cine_count = sum(texto_completo.count(self.normalize_text(kw)) 
                           for kw in cine_keywords)
            
            arte_keywords = ['pintor', 'artista', 'obra', 'cuadro', 'escultor',
                           'creador', 'museo', 'exposicion']
            arte_count = sum(texto_completo.count(self.normalize_text(kw)) 
                           for kw in arte_keywords)
            
            # Si tiene más referencias a cine que a arte, no es pintor
            if cine_count > arte_count and cine_count > 3:
                return True, f"Actor/Director (cine:{cine_count} vs arte:{arte_count})"
        
        # 3. Validación por palabras clave requeridas (solo para categorías críticas)
        if category in ['indigenous_peoples', 'painters']:
            required = self.required_keywords.get(category, [])
            if required:
                texto_completo = ""
                for p in preguntas:
                    texto_completo += self.normalize_text(p.get('pregunta', '')) + " "
                    texto_completo += self.normalize_text(p.get('respuesta_correcta', '')) + " "
                
                # Verificar si al menos 1 palabra clave aparece
                has_keyword = any(self.normalize_text(kw) in texto_completo 
                                for kw in required)
                
                if not has_keyword:
                    return True, f"No contiene palabras clave de {category}"
        
        return False, ""
    
    def clean_subset(self, input_file: str, output_file: str):
        """Limpia el subset eliminando entidades incorrectas"""
        print(f"\n{'='*80}")
        print("LIMPIEZA AUTOMÁTICA DEL SUBSET")
        print(f"{'='*80}\n")
        
        # Leer subset
        print(f"📖 Leyendo {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Estadísticas
        stats = {
            'original': {},
            'removed': {},
            'final': {},
            'reasons': {}
        }
        
        # Limpiar cada categoría
        cleaned_data = {}
        
        for category in ['indigenous_peoples', 'dances', 'painters', 'movies', 'landmarks']:
            items = data.get(category, [])
            stats['original'][category] = len(items)
            stats['removed'][category] = 0
            stats['reasons'][category] = []
            
            cleaned_items = []
            
            for item in items:
                should_remove, reason = self.should_remove_entity(category, item)
                
                if should_remove:
                    stats['removed'][category] += 1
                    entidad = item.get('entidad', '')
                    stats['reasons'][category].append((entidad, reason))
                else:
                    cleaned_items.append(item)
            
            cleaned_data[category] = cleaned_items
            stats['final'][category] = len(cleaned_items)
        
        # Guardar subset limpio
        print(f"\n💾 Guardando {output_file}...\n")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
        
        # Mostrar resultados
        print(f"{'='*80}")
        print("RESULTADOS DE LIMPIEZA")
        print(f"{'='*80}\n")
        
        for category in ['indigenous_peoples', 'dances', 'painters', 'movies', 'landmarks']:
            orig = stats['original'][category]
            removed = stats['removed'][category]
            final = stats['final'][category]
            
            print(f"{category.upper().replace('_', ' ')}:")
            print(f"  Original:  {orig:3d} entidades")
            print(f"  Eliminadas: {removed:3d} entidades")
            print(f"  Final:     {final:3d} entidades")
            
            if stats['reasons'][category]:
                print(f"  Entidades eliminadas:")
                for entidad, reason in stats['reasons'][category][:5]:  # Top 5
                    print(f"    ❌ {entidad[:50]:50s} - {reason}")
                if len(stats['reasons'][category]) > 5:
                    print(f"    ... y {len(stats['reasons'][category]) - 5} más")
            print()
        
        # Resumen final
        total_orig = sum(stats['original'].values())
        total_removed = sum(stats['removed'].values())
        total_final = sum(stats['final'].values())
        
        # Calcular preguntas
        total_q_orig = sum(
            sum(len(item['preguntas']) for item in data.get(cat, []))
            for cat in data
        )
        total_q_final = sum(
            sum(len(item['preguntas']) for item in cleaned_data.get(cat, []))
            for cat in cleaned_data
        )
        
        print(f"{'='*80}")
        print("RESUMEN GENERAL")
        print(f"{'='*80}")
        print(f"Entidades originales:  {total_orig}")
        print(f"Entidades eliminadas:  {total_removed} ({total_removed/total_orig*100:.1f}%)")
        print(f"Entidades finales:     {total_final}")
        print(f"\nPreguntas originales:  {total_q_orig}")
        print(f"Preguntas finales:     {total_q_final}")
        print(f"Preguntas eliminadas:  {total_q_orig - total_q_final}")
        print(f"{'='*80}\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Limpieza automática de subset_h2_final.json'
    )
    parser.add_argument(
        '--input',
        default='subset_h2_final.json',
        help='Archivo de entrada (default: subset_h2_final.json)'
    )
    parser.add_argument(
        '--output',
        default='subset_h2_limpio.json',
        help='Archivo de salida (default: subset_h2_limpio.json)'
    )
    
    args = parser.parse_args()
    
    cleaner = SubsetCleaner()
    cleaner.clean_subset(args.input, args.output)
    
    print("✨ LIMPIEZA COMPLETADA ✨\n")
    print(f"Archivo limpio guardado en: {args.output}")


if __name__ == '__main__':
    main()
