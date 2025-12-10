#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script MEJORADO para minar dataset_benchmark_qa.json
Extrae subset balanceado con categorización PRECISA de las 5 categorías
"""

import json
import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import argparse


class DatasetMinerMejorado:
    """Minero mejorado con reglas estrictas de categorización"""
    
    def __init__(self):
        # Keywords más específicas y precisas
        self.category_rules = {
            'painters': {
                # REGLA ESTRICTA: Solo si la ocupación incluye pintor
                'must_have_respuesta': ['pintor', 'muralista', 'pintura'],
                'must_have_pregunta': ['ocupacion', 'artista'],
                'exclude': ['actor', 'politico', 'futbol']
            },
            'dances': {
                # REGLA: Géneros musicales/danzas, NO personas
                'must_have': ['samba', 'tango', 'cumbia', 'salsa', 'merengue', 'bachata',
                             'folklore', 'cueca', 'marinera', 'joropo', 'chacarera',
                             'zamba', 'huayno', 'son', 'danzon', 'bolero', 'frevo',
                             'jongo', 'carimbó', 'ciranda', 'forro', 'lambada',
                             'genero musical', 'danza tradicional', 'baile folklorico'],
                'exclude': ['ocupacion de', 'lugar de nacimiento', 'ser humano']
            },
            'indigenous_peoples': {
                # REGLA: Pueblos indígenas específicos
                'must_have': ['mapuche', 'quechua', 'aymara', 'guarani', 'maya', 'azteca',
                             'inca', 'pueblo indigena', 'etnia', 'yaminahua', 'kayapo',
                             'satere-mawe', 'tabajara', 'pueblo originario',
                             'comunidad indigena', 'nacion indigena', 'tribu', 'ancestral'],
                'exclude': []
            },
            'movies': {
                # REGLA: Solo películas y programas de TV
                'must_have_pregunta': ['genero de', 'director de', 'miembro del reparto',
                                      'idioma de la pelicula', 'programa de television'],
                'must_have_respuesta': ['accion', 'comedia', 'drama', 'terror', 'suspenso',
                                        'ciencia ficcion', 'aventura', 'romance', 'animacion'],
                'or_in_respuesta': ['pelicula', 'film', 'cine'],
                'exclude': []
            },
            'landmarks': {
                # REGLA: Lugares geográficos y monumentos
                'must_have': ['machu picchu', 'cristo redentor', 'cataratas', 'obelisco',
                             'casa rosada', 'palacio de la moneda', 'catedral', 'basilica',
                             'monumento', 'patrimonio', 'landmark', 'sitio arqueologico'],
                'or_in_pregunta': ['ubicacion administrativa', 'situado en la entidad',
                                   'coordenadas', 'patrimonio'],
                'exclude': ['ocupacion', 'partido politico', 'ministerio']
            }
        }
    
    def normalize_text(self, text: str) -> str:
        """Normaliza texto"""
        if not text:
            return ""
        text = text.lower().strip()
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u', 'à': 'a', 'è': 'e', 'ì': 'i',
            'ò': 'o', 'ù': 'u', 'ã': 'a', 'õ': 'o', 'ç': 'c'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    def categorize_question(self, pregunta: str, respuesta: str) -> str:
        """
        Categoriza una pregunta usando REGLAS ESTRICTAS
        """
        preg_norm = self.normalize_text(pregunta)
        resp_norm = self.normalize_text(respuesta)
        
        # PRIORIDAD 1: PAINTERS (ocupación = pintor)
        if 'ocupacion' in preg_norm and 'pintor' in resp_norm:
            # Verificar exclusiones
            if not any(ex in resp_norm for ex in self.category_rules['painters']['exclude']):
                return 'painters'
        
        # PRIORIDAD 2: INDIGENOUS_PEOPLES (pueblos indígenas específicos)
        for keyword in self.category_rules['indigenous_peoples']['must_have']:
            if keyword in preg_norm or keyword in resp_norm:
                return 'indigenous_peoples'
        
        # PRIORIDAD 3: DANCES (géneros musicales/danzas)
        for keyword in self.category_rules['dances']['must_have']:
            if keyword in preg_norm or keyword in resp_norm:
                # Verificar que no sea sobre una persona
                if not any(ex in preg_norm for ex in self.category_rules['dances']['exclude']):
                    return 'dances'
        
        # PRIORIDAD 4: MOVIES (películas)
        if any(kw in preg_norm for kw in self.category_rules['movies']['must_have_pregunta']):
            if any(kw in resp_norm for kw in self.category_rules['movies']['must_have_respuesta']):
                return 'movies'
        
        # PRIORIDAD 5: LANDMARKS (lugares)
        if any(kw in preg_norm for kw in self.category_rules['landmarks'].get('or_in_pregunta', [])):
            if not any(ex in preg_norm or ex in resp_norm for ex in self.category_rules['landmarks']['exclude']):
                return 'landmarks'
        
        for keyword in self.category_rules['landmarks']['must_have']:
            if keyword in preg_norm or keyword in resp_norm:
                return 'landmarks'
        
        return None  # No categorizada
    
    def extract_entity(self, pregunta: str) -> str:
        """Extrae la entidad de la pregunta"""
        patterns = [
            r'¿Cuál es .+ de (.+)\?',
            r'de (.+)\?$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, pregunta)
            if match:
                return match.group(1).strip()
        
        return pregunta.replace('¿', '').replace('?', '').strip()
    
    def mine(self, input_file: str, samples: int = 25) -> Dict:
        """Mina el dataset y extrae subset balanceado"""
        
        print("="*80)
        print(f"MINERÍA MEJORADA: {input_file}")
        print("="*80)
        
        # Leer dataset
        print("\n📖 Leyendo dataset...")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✓ {len(data):,} preguntas cargadas")
        
        # Categorizar y agrupar por entidad
        print("\n🔍 Categorizando con REGLAS MEJORADAS...")
        
        category_entities = defaultdict(lambda: defaultdict(list))
        total_categorized = 0
        
        for i, item in enumerate(data, 1):
            if i % 10000 == 0:
                print(f"  Procesadas {i:,} preguntas...")
            
            pregunta = item.get('pregunta', '')
            respuesta = item.get('respuesta_correcta', '')
            
            category = self.categorize_question(pregunta, respuesta)
            
            if category:
                entity = self.extract_entity(pregunta)
                category_entities[category][entity].append({
                    'pregunta': pregunta,
                    'respuesta_correcta': respuesta
                })
                total_categorized += 1
        
        print(f"\n✓ {total_categorized:,} preguntas categorizadas")
        
        # Estadísticas
        print("\n" + "="*80)
        print("ESTADÍSTICAS")
        print("="*80)
        
        for cat in ['indigenous_peoples', 'dances', 'painters', 'movies', 'landmarks']:
            if cat in category_entities:
                num_entities = len(category_entities[cat])
                num_preguntas = sum(len(preg_list) for preg_list in category_entities[cat].values())
                print(f"{cat:25s}: {num_preguntas:6d} preguntas | {num_entities:5d} entidades")
        
        # Extraer subset
        print("\n" + "="*80)
        print(f"EXTRAYENDO SUBSET ({samples} entidades por categoría)")
        print("="*80)
        
        subset = {}
        
        for cat in ['indigenous_peoples', 'dances', 'painters', 'movies', 'landmarks']:
            if cat not in category_entities:
                print(f"\n⚠️  {cat}: No hay entidades")
                continue
            
            # Ordenar entidades por número de preguntas (descendente)
            sorted_entities = sorted(
                category_entities[cat].items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
            
            # Tomar las top N entidades
            top_entities = sorted_entities[:samples]
            
            subset[cat] = []
            total_preg = 0
            
            for entity, preguntas in top_entities:
                subset[cat].append({
                    'entidad': entity,
                    'preguntas': preguntas,
                    'category': cat
                })
                total_preg += len(preguntas)
            
            print(f"\n✓ {cat:25s}: {len(top_entities):3d} entidades | {total_preg:4d} preguntas")
            
            # Mostrar top 5
            print(f"  Top entidades:")
            for i, (entity, preguntas) in enumerate(top_entities[:5], 1):
                print(f"    {i}. {entity:50s} ({len(preguntas):3d} preguntas)")
        
        return subset
    
    def save_subset(self, subset: Dict, output_file: str):
        """Guarda el subset"""
        print("\n" + "="*80)
        print(f"GUARDANDO: {output_file}")
        print("="*80)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(subset, f, ensure_ascii=False, indent=4)
        
        total_entities = sum(len(items) for items in subset.values())
        total_questions = sum(
            sum(len(item['preguntas']) for item in items)
            for items in subset.values()
        )
        
        print(f"\n✓ Total entidades: {total_entities}")
        print(f"✓ Total preguntas: {total_questions}")
        print(f"✓ Archivo: {output_file}")
        
        print("\n" + "="*80)
        print("✨ MINERÍA COMPLETADA ✨")
        print("="*80)


def main():
    parser = argparse.ArgumentParser(description='Minar dataset con categorización mejorada')
    parser.add_argument('--input', default='dataset_benchmark_qa.json',
                       help='Archivo de entrada')
    parser.add_argument('--output', default='subset_h2_mejorado.json',
                       help='Archivo de salida')
    parser.add_argument('--samples', type=int, default=25,
                       help='Número de entidades por categoría')
    
    args = parser.parse_args()
    
    miner = DatasetMinerMejorado()
    subset = miner.mine(args.input, args.samples)
    miner.save_subset(subset, args.output)


if __name__ == '__main__':
    main()
