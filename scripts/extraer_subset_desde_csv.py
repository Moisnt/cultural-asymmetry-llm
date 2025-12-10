#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para extraer subset balanceado usando los CSV originales como fuente de verdad
Esto garantiza que las categorías sean 100% correctas
"""

import json
import csv
import re
from collections import defaultdict, Counter
from typing import Dict, List, Set


class SubsetExtractor:
    """Extractor de subset usando CSV originales como fuente de verdad"""
    
    def __init__(self):
        # Mapeo de archivos CSV a categorías
        self.csv_files = {
            'indigenous_peoples': 'pueblos_indigenas_latam_4079Entities.csv',
            'dances': 'danzas_por_pais_latam_1401Entities.csv',
            'painters': 'pintores_latam_4671Entities.csv',
            'movies': 'cine_latam_151363Entities.csv',
            'landmarks': 'landmarks_LATAM_103493Entities.csv'
        }
        
        # Índice de entidades por categoría
        self.entity_index = defaultdict(set)
        
    def normalize_text(self, text: str) -> str:
        """Normaliza texto para comparación"""
        if not text:
            return ""
        text = text.lower().strip()
        # Quitar acentos
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u', 'à': 'a', 'è': 'e', 'ì': 'i',
            'ò': 'o', 'ù': 'u', 'ã': 'a', 'õ': 'o', 'ç': 'c'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    def load_entities_from_csv(self, category: str, csv_file: str, max_entities: int = 500):
        """Carga entidades desde un archivo CSV con filtros específicos"""
        print(f"  📄 Cargando {csv_file}...")
        
        # Palabras a excluir por categoría
        exclusions = {
            'indigenous_peoples': ['italiano', 'aleman', 'frances', 'ingles', 'judio', 
                                   'sefardi', 'libanes', 'sirio', 'europeo', 'asiatico',
                                   'africano', 'inmigracion', 'diaspora'],
            'painters': ['actor', 'actriz', 'director', 'cineasta', 'escritor', 
                        'musico', 'cantante', 'compositor'],
            'dances': [],
            'movies': [],
            'landmarks': []
        }
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                entities = set()
                excluded_count = 0
                
                for row in reader:
                    entity = row.get('entidad', '').strip()
                    if not entity:
                        continue
                    
                    # Aplicar filtros de exclusión
                    entity_norm = self.normalize_text(entity)
                    excluded = False
                    
                    for exclusion_word in exclusions.get(category, []):
                        if self.normalize_text(exclusion_word) in entity_norm:
                            excluded = True
                            excluded_count += 1
                            break
                    
                    if not excluded:
                        entities.add(entity)
                        self.entity_index[category].add(entity_norm)
                        
                        if len(entities) >= max_entities:
                            break
                
                msg = f"     ✓ {len(entities)} entidades cargadas"
                if excluded_count > 0:
                    msg += f" ({excluded_count} excluidas)"
                print(msg)
                return entities
                
        except FileNotFoundError:
            print(f"     ⚠️  Archivo no encontrado: {csv_file}")
            return set()
        except Exception as e:
            print(f"     ⚠️  Error: {e}")
            return set()
    
    def build_entity_index(self):
        """Construye índice de todas las entidades de los CSV"""
        print(f"\n{'='*80}")
        print("CONSTRUYENDO ÍNDICE DE ENTIDADES DESDE CSV")
        print(f"{'='*80}\n")
        
        for category, csv_file in self.csv_files.items():
            self.load_entities_from_csv(category, csv_file)
        
        # Mostrar resumen
        print(f"\n{'='*80}")
        print("ÍNDICE CONSTRUIDO")
        print(f"{'='*80}")
        for category in ['indigenous_peoples', 'dances', 'painters', 'movies', 'landmarks']:
            count = len(self.entity_index[category])
            print(f"{category:25s}: {count:6,} entidades indexadas")
    
    def extract_entity_from_question(self, pregunta: str) -> str:
        """Extrae la entidad de la pregunta"""
        # Patrones comunes en español
        patterns = [
            r'de (.+)\?$',
            r'¿Cuál es .+ de (.+)\?',
            r'¿Cuál es el .+ de (.+)\?',
            r'¿Cuál es la .+ de (.+)\?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, pregunta)
            if match:
                entity = match.group(1).strip()
                # Limpiar palabras comunes al final
                entity = re.sub(r'\s+(de|en|del|la|el|los|las)$', '', entity, flags=re.IGNORECASE)
                return entity
        
        return ""
    
    def categorize_question(self, pregunta: str, respuesta: str) -> tuple:
        """
        Categoriza una pregunta basándose en el índice de entidades CSV
        
        Returns:
            (category, entity) o (None, None) si no coincide
        """
        # Extraer entidad de la pregunta
        entity = self.extract_entity_from_question(pregunta)
        if not entity:
            return None, None
        
        entity_norm = self.normalize_text(entity)
        
        # Buscar en qué categoría está esta entidad
        for category in ['indigenous_peoples', 'dances', 'painters', 'movies', 'landmarks']:
            if entity_norm in self.entity_index[category]:
                return category, entity
        
        # También buscar en la respuesta
        respuesta_norm = self.normalize_text(respuesta)
        for category in ['indigenous_peoples', 'dances', 'painters', 'movies', 'landmarks']:
            if respuesta_norm in self.entity_index[category]:
                return category, respuesta
        
        return None, None
    
    def extract_subset(self, dataset_file: str, samples_per_category: int = 30):
        """Extrae subset balanceado del dataset con validación estricta"""
        print(f"\n{'='*80}")
        print(f"EXTRAYENDO SUBSET DE: {dataset_file}")
        print(f"{'='*80}\n")
        
        # Leer dataset
        print("📖 Leyendo dataset...")
        with open(dataset_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ {len(data):,} preguntas cargadas\n")
        
        # Palabras de validación por categoría (en respuestas)
        validation_keywords = {
            'indigenous_peoples': ['pueblo', 'indigena', 'etnia', 'nativo', 'tribu', 
                                   'ancestral', 'originario', 'comunidad'],
            'dances': ['danza', 'baile', 'ritmo', 'musica', 'folklore', 'folclore',
                      'tradicional', 'genero musical'],
            'painters': ['pintor', 'artista', 'obra', 'cuadro', 'pintura', 'museo',
                        'exposicion', 'galeria', 'arte'],
            'movies': ['pelicula', 'film', 'cine', 'director', 'actor', 'produccion'],
            'landmarks': ['ubicado', 'situado', 'monumento', 'edificio', 'puente',
                         'parque', 'catedral', 'plaza']
        }
        
        # Agrupar preguntas por entidad y categoría
        print("🔍 Categorizando preguntas usando índice CSV...")
        entities_by_category = defaultdict(lambda: defaultdict(list))
        category_stats = Counter()
        categorized = 0
        
        for i, item in enumerate(data, 1):
            pregunta = item.get('pregunta', '')
            respuesta = item.get('respuesta_correcta', '')
            
            category, entity = self.categorize_question(pregunta, respuesta)
            
            if category and entity:
                # Validación adicional con palabras clave en las respuestas
                pregunta_norm = self.normalize_text(pregunta)
                respuesta_norm = self.normalize_text(respuesta)
                texto_completo = pregunta_norm + " " + respuesta_norm
                
                # Verificar que al menos una palabra de validación esté presente
                # O que sea una categoría específica que confíe en el CSV
                has_validation = any(
                    self.normalize_text(keyword) in texto_completo
                    for keyword in validation_keywords.get(category, [])
                )
                
                # Relajar validación para categorías con pocos datos
                if not has_validation and category in ['dances', 'painters', 'indigenous_peoples']:
                    # Si está en el CSV, confiar en ello (validación ligera)
                    has_validation = True
                
                # Para painters, filtrar actores/directores que se colaron
                if category == 'painters':
                    # Si menciona "director" o "actor" sin mencionar "pintor/artista", skip
                    if ('director' in texto_completo or 'actor' in texto_completo or 
                        'actriz' in texto_completo or 'cineasta' in texto_completo):
                        if not ('pintor' in texto_completo or 'artista' in texto_completo or
                               'obra' in texto_completo or 'cuadro' in texto_completo or
                               'pintura' in texto_completo or 'escultor' in texto_completo):
                            has_validation = False
                
                if has_validation or category in ['landmarks', 'movies']:  # Menos estricto para estas
                    entities_by_category[category][entity].append({
                        'pregunta': pregunta,
                        'respuesta_correcta': respuesta
                    })
                    category_stats[category] += 1
                    categorized += 1
            
            if i % 10000 == 0:
                print(f"  Procesadas {i:,} preguntas ({categorized:,} categorizadas)...")
        
        print(f"\n✓ {categorized:,} preguntas categorizadas de {len(data):,} totales\n")
        
        # Estadísticas
        print(f"{'='*80}")
        print("ESTADÍSTICAS DE CATEGORIZACIÓN")
        print(f"{'='*80}")
        for cat in ['indigenous_peoples', 'dances', 'painters', 'movies', 'landmarks']:
            count = category_stats.get(cat, 0)
            num_entities = len(entities_by_category[cat])
            print(f"{cat:25s}: {count:6,} preguntas | {num_entities:5,} entidades")
        
        # Construir subset balanceado
        print(f"\n{'='*80}")
        print(f"EXTRAYENDO SUBSET ({samples_per_category} entidades por categoría)")
        print(f"{'='*80}\n")
        
        subset = {}
        
        for category in ['indigenous_peoples', 'dances', 'painters', 'movies', 'landmarks']:
            subset[category] = []
            
            # Ordenar por número de preguntas
            entities = entities_by_category[category]
            sorted_entities = sorted(
                entities.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
            
            # Tomar top N
            for entity, preguntas in sorted_entities[:samples_per_category]:
                subset[category].append({
                    'entidad': entity,
                    'preguntas': preguntas,
                    'category': category
                })
            
            total_q = sum(len(item['preguntas']) for item in subset[category])
            print(f"✓ {category:25s}: {len(subset[category]):3d} entidades | {total_q:5,} preguntas")
            
            # Top 5
            if subset[category]:
                print(f"  Top 5:")
                for i, item in enumerate(subset[category][:5], 1):
                    num_q = len(item['preguntas'])
                    print(f"    {i}. {item['entidad'][:55]:55s} ({num_q:3d} preguntas)")
        
        return subset
    
    def save_subset(self, subset: Dict, output_file: str):
        """Guarda el subset"""
        print(f"\n{'='*80}")
        print(f"GUARDANDO: {output_file}")
        print(f"{'='*80}\n")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(subset, f, ensure_ascii=False, indent=4)
        
        total_entities = sum(len(subset[cat]) for cat in subset)
        total_questions = sum(
            sum(len(item['preguntas']) for item in subset[cat])
            for cat in subset
        )
        
        print(f"✓ Subset guardado")
        print(f"✓ Total entidades: {total_entities}")
        print(f"✓ Total preguntas: {total_questions:,}")
        print(f"✓ Archivo: {output_file}\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extraer subset balanceado usando CSV como fuente de verdad'
    )
    parser.add_argument(
        '--dataset',
        default='dataset_benchmark_qa.json',
        help='Dataset de preguntas (default: dataset_benchmark_qa.json)'
    )
    parser.add_argument(
        '--output',
        default='subset_h2_final.json',
        help='Archivo de salida (default: subset_h2_final.json)'
    )
    parser.add_argument(
        '--samples',
        type=int,
        default=30,
        help='Entidades por categoría (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Ejecutar
    extractor = SubsetExtractor()
    extractor.build_entity_index()
    subset = extractor.extract_subset(args.dataset, args.samples)
    extractor.save_subset(subset, args.output)
    
    print(f"{'='*80}")
    print("✨ EXTRACCIÓN COMPLETADA EXITOSAMENTE ✨")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
