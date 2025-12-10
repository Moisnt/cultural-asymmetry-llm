#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para minar dataset_benchmark_qa.json y extraer subset balanceado
con las 5 categorías de la Hipótesis 2
"""

import json
import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple


class DatasetMiner:
    """Minero de datasets para extraer y categorizar entidades"""
    
    def __init__(self):
        # Palabras clave específicas y optimizadas para cada categoría
        self.category_keywords = {
            'indigenous_peoples': {
                'entidades': [
                    'mapuche', 'quechua', 'aymara', 'guaraní', 'guarani', 'maya', 'azteca',
                    'inca', 'tolteca', 'zapoteca', 'mixteca', 'nahuatl', 'tarahumara',
                    'yaminahua', 'kayapo', 'satere-mawe', 'tabajara', 'yanomami',
                    'tupi', 'guarayu', 'wichi', 'toba', 'qom', 'diaguita', 'atacameño',
                    'atacameno', 'kawesqar', 'yagan', 'selknam', 'ona', 'tehuelche',
                    'ranquel', 'comechingon', 'huarpe', 'lule', 'vilela'
                ],
                'palabras': [
                    'indigena', 'pueblo indigena', 'pueblos indigenas', 'pueblo originario',
                    'nacion indigena', 'etnia', 'aboriginal', 'nativo', 'autoctono',
                    'precolombino', 'prehispanico', 'ancestral', 'cosmovision',
                    'lengua indigena', 'idioma indigena', 'territorio indigena',
                    'comunidad indigena', 'reserva indigena', 'tribu'
                ]
            },
            'dances': {
                'entidades': [
                    'tango', 'salsa', 'cumbia', 'bachata', 'merengue', 'samba', 'bossa nova',
                    'cueca', 'marinera', 'joropo', 'chacarera', 'zamba', 'huayno', 'huaino',
                    'son', 'danzon', 'bolero', 'milonga', 'candombe', 'vals', 'pasillo',
                    'bambuco', 'porro', 'malambo', 'gato', 'bailecito', 'carnavalito',
                    'frevo', 'jongo', 'carimbo', 'ciranda', 'forro', 'maxixe', 'choro',
                    'lambada', 'axe', 'afoxe', 'baile', 'danza'
                ],
                'palabras': [
                    'danza', 'baile', 'bailar', 'danzar', 'coreografia', 'bailarin', 'bailarina',
                    'danza tradicional', 'baile tradicional', 'danza folclorica', 'folklore',
                    'folclore', 'danza popular', 'ritmo', 'musica de baile', 'coreografo',
                    'compania de danza', 'genero de danza', 'estilo de baile', 'dance',
                    'dancing', 'folk dance', 'traditional dance'
                ]
            },
            'painters': {
                'entidades': [
                    'diego rivera', 'frida kahlo', 'rufino tamayo', 'david alfaro siqueiros',
                    'jose clemente orozco', 'roberto matta', 'fernando botero',
                    'oswaldo guayasamin', 'joaquin torres garcia', 'wilfredo lam',
                    'remedios varo', 'leonora carrington', 'ernesto sabato', 'cándido portinari',
                    'candido portinari', 'tarsila do amaral', 'xul solar', 'emilio pettoruti',
                    'antonio berni', 'benito quinquela martin', 'raul soldi', 'lino enea spilimbergo',
                    'rodrigo arenas betancourt', 'francisco zuniga', 'claudio bravo',
                    'roberto matta', 'nemesio antunez', 'jose balmes', 'guillermo nunez'
                ],
                'palabras': [
                    'pintor', 'pintora', 'artista plastico', 'artista visual', 'obra pictorica',
                    'cuadro', 'lienzo', 'oleo', 'acuarela', 'mural', 'muralista', 'retrato',
                    'paisaje', 'bodegon', 'pintura', 'exposicion', 'galeria', 'museo de arte',
                    'coleccion', 'estilo pictorico', 'movimiento artistico', 'painter', 'artist',
                    'artwork', 'painting', 'canvas', 'exhibition', 'painted', 'drew',
                    'obra de arte', 'artista', 'escultor', 'grabador'
                ]
            },
            'movies': {
                'entidades': [
                    'casino royale', 'iron man', 'moonraker', 'spy game', 'grindhouse',
                    'planet terror', 'el secreto de sus ojos', 'relatos salvajes',
                    'nueve reinas', 'ciudad de dios', 'central do brasil', 'tropa de elite',
                    'y tu mama tambien', 'amores perros', 'el laberinto del fauno',
                    'pan\'s labyrinth', 'roma', 'la historia oficial', 'el hijo de la novia',
                    'diarios de motocicleta', 'no', 'gloria', 'machuca', 'la teta asustada'
                ],
                'palabras': [
                    'pelicula', 'film', 'cine', 'cinematografia', 'director de fotografia',
                    'miembro del reparto', 'cast member', 'actor', 'actriz', 'genero cinematografico',
                    'idioma de la pelicula', 'programa de television', 'serie', 'episodio',
                    'emisora', 'broadcaster', 'estreno', 'premiere', 'productor', 'producer',
                    'guion', 'screenplay', 'screenwriter', 'director', 'film director', 'movie',
                    'cinema', 'box office', 'filming', 'produccion cinematografica',
                    'industria del cine', 'distribuidor', 'distribucion'
                ]
            },
            'landmarks': {
                'entidades': [
                    'machu picchu', 'cristo redentor', 'iguazu', 'cataratas', 'obelisco',
                    'torre eiffel', 'coliseo', 'taj mahal', 'gran muralla', 'estatua libertad',
                    'casa rosada', 'palacio de la moneda', 'congreso', 'catedral',
                    'basilica', 'templo', 'museo', 'teatro colon', 'opera', 'estadio'
                ],
                'palabras': [
                    'landmark', 'monumento', 'sitio', 'ubicado', 'situado', 'capital',
                    'provincia', 'region', 'municipio', 'departamento', 'frontera',
                    'entidad territorial', 'administrative', 'located in', 'coordenadas',
                    'aeropuerto', 'estadio', 'plaza', 'edificio', 'construccion',
                    'infraestructura', 'terminal', 'puente', 'iglesia', 'parque',
                    'direccion postal', 'patrimonio', 'heritage'
                ]
            }
        }
        
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
    
    def extract_entity_from_question(self, pregunta: str) -> str:
        """Extrae la entidad principal de la pregunta"""
        # Patrones comunes
        patterns = [
            r'¿Cuál es .+ de (.+)\?',
            r'¿Cuál es el .+ de (.+)\?',
            r'¿Cuál es la .+ de (.+)\?',
            r'¿Cuál es un .+ de (.+)\?',
            r'¿Cuál es una .+ de (.+)\?',
            r'de (.+)\?$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, pregunta, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Si no hay patrón, retornar la pregunta sin signos
        return pregunta.replace('¿', '').replace('?', '').strip()
    
    def detect_category(self, pregunta: str, respuesta: str) -> str:
        """Detecta la categoría de una pregunta"""
        # Texto combinado para análisis
        texto = self.normalize_text(f"{pregunta} {respuesta}")
        
        # Calcular scores
        scores = defaultdict(int)
        
        for category, keywords in self.category_keywords.items():
            # Entidades específicas (peso alto)
            for keyword in keywords['entidades']:
                keyword_norm = self.normalize_text(keyword)
                if keyword_norm in texto:
                    # Palabras completas valen más
                    if re.search(r'\b' + re.escape(keyword_norm) + r'\b', texto):
                        scores[category] += 10
                    else:
                        scores[category] += 5
            
            # Palabras clave contextuales
            for keyword in keywords['palabras']:
                keyword_norm = self.normalize_text(keyword)
                if keyword_norm in texto:
                    scores[category] += texto.count(keyword_norm)
        
        # Reglas de desambiguación
        if scores['indigenous_peoples'] > 0:
            scores['indigenous_peoples'] += 15  # Máxima prioridad
        
        if scores['dances'] > 0:
            scores['dances'] += 12
        
        if scores['painters'] > 0:
            scores['painters'] += 10
        
        if scores['movies'] > 0:
            scores['movies'] += 8
        
        # Si no hay score, retornar None
        if max(scores.values()) == 0:
            return None
        
        return max(scores, key=scores.get)
    
    def mine_dataset(self, input_file: str, samples_per_category: int = 30) -> Dict:
        """
        Mina el dataset y extrae un subset balanceado
        
        Args:
            input_file: Archivo JSON de entrada
            samples_per_category: Número de entidades por categoría
            
        Returns:
            Dict con el subset organizado por categorías
        """
        print(f"\n{'='*80}")
        print(f"MINANDO DATASET: {input_file}")
        print(f"{'='*80}\n")
        
        # Leer dataset
        print("📖 Leyendo dataset...")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✓ {len(data):,} preguntas cargadas\n")
        
        # Agrupar por entidad y categoría
        print("🔍 Categorizando preguntas...")
        entities_by_category = defaultdict(lambda: defaultdict(list))
        category_stats = Counter()
        processed = 0
        
        for item in data:
            pregunta = item.get('pregunta', '')
            respuesta = item.get('respuesta_correcta', '')
            
            # Detectar categoría
            category = self.detect_category(pregunta, respuesta)
            
            if category:
                # Extraer entidad
                entity = self.extract_entity_from_question(pregunta)
                
                # Guardar pregunta agrupada por entidad
                entities_by_category[category][entity].append({
                    'pregunta': pregunta,
                    'respuesta_correcta': respuesta
                })
                
                category_stats[category] += 1
            
            processed += 1
            if processed % 10000 == 0:
                print(f"  Procesadas {processed:,} preguntas...")
        
        print(f"\n✓ Procesamiento completo: {processed:,} preguntas\n")
        
        # Mostrar estadísticas
        print(f"{'='*80}")
        print("ESTADÍSTICAS DE CATEGORIZACIÓN")
        print(f"{'='*80}")
        for cat in ['indigenous_peoples', 'dances', 'painters', 'movies', 'landmarks']:
            count = category_stats.get(cat, 0)
            num_entities = len(entities_by_category[cat])
            print(f"{cat:25s}: {count:6,} preguntas | {num_entities:5,} entidades únicas")
        
        # Construir subset balanceado
        print(f"\n{'='*80}")
        print(f"EXTRAYENDO SUBSET BALANCEADO ({samples_per_category} entidades por categoría)")
        print(f"{'='*80}\n")
        
        subset = {}
        
        for category in ['indigenous_peoples', 'dances', 'painters', 'movies', 'landmarks']:
            subset[category] = []
            
            # Ordenar entidades por número de preguntas (descendente)
            entities = entities_by_category[category]
            sorted_entities = sorted(
                entities.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
            
            # Tomar las top N entidades
            count = 0
            for entity, preguntas in sorted_entities[:samples_per_category]:
                subset[category].append({
                    'entidad': entity,
                    'preguntas': preguntas,
                    'category': category
                })
                count += 1
            
            total_questions = sum(len(item['preguntas']) for item in subset[category])
            print(f"✓ {category:25s}: {count:3d} entidades | {total_questions:5,} preguntas")
            
            # Mostrar top 5
            if subset[category]:
                print(f"  Top entidades:")
                for i, item in enumerate(subset[category][:5], 1):
                    print(f"    {i}. {item['entidad'][:60]:60s} ({len(item['preguntas']):3d} preguntas)")
        
        return subset
    
    def save_subset(self, subset: Dict, output_file: str):
        """Guarda el subset en formato JSON"""
        print(f"\n{'='*80}")
        print(f"GUARDANDO SUBSET: {output_file}")
        print(f"{'='*80}\n")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(subset, f, ensure_ascii=False, indent=4)
        
        # Calcular totales
        total_entities = sum(len(subset[cat]) for cat in subset)
        total_questions = sum(
            sum(len(item['preguntas']) for item in subset[cat])
            for cat in subset
        )
        
        print(f"✓ Subset guardado exitosamente")
        print(f"✓ Total de entidades: {total_entities}")
        print(f"✓ Total de preguntas: {total_questions:,}")
        print(f"✓ Archivo: {output_file}\n")


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Minar dataset_benchmark_qa.json y extraer subset balanceado (Hipótesis 2)'
    )
    parser.add_argument(
        '--input',
        default='dataset_benchmark_qa.json',
        help='Archivo JSON de entrada (default: dataset_benchmark_qa.json)'
    )
    parser.add_argument(
        '--output',
        default='subset_h2_balanceado.json',
        help='Archivo JSON de salida (default: subset_h2_balanceado.json)'
    )
    parser.add_argument(
        '--samples',
        type=int,
        default=30,
        help='Número de entidades por categoría (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Ejecutar minería
    miner = DatasetMiner()
    subset = miner.mine_dataset(args.input, args.samples)
    miner.save_subset(subset, args.output)
    
    print(f"{'='*80}")
    print("✨ MINERÍA COMPLETADA EXITOSAMENTE ✨")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
