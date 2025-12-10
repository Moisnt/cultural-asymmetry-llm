#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para agregar categorías automáticas al dataset de preguntas
Detecta categorías basadas en palabras clave y contexto de las preguntas
"""

import json
import re
from typing import Dict, List, Set
from collections import Counter


class DatasetCategorizer:
    """Clase para categorizar automáticamente entradas del dataset"""
    
    def __init__(self):
        # Definir palabras clave para las 5 categorías específicas del proyecto (Hipótesis 2)
        self.category_keywords = {
            'landmarks': {
                'entidades': [
                    'chile', 'argentina', 'perú', 'peru', 'méxico', 'mexico', 'colombia', 
                    'buenos aires', 'santiago', 'lima', 'córdoba', 'cordoba', 'viña del mar',
                    'la plata', 'concepción', 'concepcion', 'montevideo', 'bogotá', 'bogota',
                    'medellin', 'medellín', 'quito', 'ecuador', 'guayaquil', 'venezuela',
                    'aeropuerto', 'estadio', 'plaza', 'calle', 'avenida', 'biblioteca',
                    'estación', 'estacion', 'mirador', 'capilla', 'catedral', 'monumento',
                    'parque', 'puente', 'edificio', 'museo', 'galería', 'galeria'
                ],
                'palabras': [
                    'landmark', 'punto de interes', 'lugar emblemático', 'lugar emblematico',
                    'monumento', 'sitio', 'ubicado', 'situado', 'capital', 'provincia',
                    'región', 'region', 'municipio', 'departamento', 'frontera', 'territorio',
                    'entidad territorial', 'administrative', 'located in', 'shares border',
                    'geografía', 'geografia', 'lugar', 'localización', 'localizacion',
                    'coordenadas', 'superficie', 'población', 'poblacion', 'habitantes',
                    'aeropuerto', 'estadio', 'plaza', 'edificio', 'construcción', 'construccion',
                    'infraestructura', 'terminal', 'puente', 'catedral', 'iglesia', 'capilla',
                    'museo', 'parque', 'dirección postal', 'direccion postal', 'hub', 'transport'
                ]
            },
            'indigenous_peoples': {
                'entidades': [
                    'mapuche', 'quechua', 'aymara', 'guaraní', 'guarani', 'maya', 'azteca',
                    'inca', 'tolteca', 'zapoteca', 'mixteca', 'pueblo indigena', 'pueblos indigenas',
                    'pueblo originario', 'pueblos originarios', 'comunidad indigena',
                    'nación', 'nacion', 'etnia', 'tribu'
                ],
                'palabras': [
                    'indígena', 'indigena', 'pueblo indigena', 'pueblos indigenas',
                    'pueblo originario', 'pueblos originarios', 'comunidad indigena',
                    'nación indigena', 'nacion indigena', 'etnia', 'tribu', 'ancestral',
                    'originario', 'nativo', 'autóctono', 'autoctono', 'precolombino',
                    'prehispánico', 'prehispanico', 'cosmovisión', 'cosmovision',
                    'tradición ancestral', 'tradicion ancestral', 'lengua indigena',
                    'idioma indigena', 'cultura indigena', 'territorio indigena',
                    'indigenous', 'native', 'aboriginal', 'tribal', 'ethnic group'
                ]
            },
            'painters': {
                'entidades': [
                    'diego rivera', 'frida kahlo', 'rufino tamayo', 'david alfaro siqueiros',
                    'josé clemente orozco', 'jose clemente orozco', 'roberto matta',
                    'fernando botero', 'oswaldo guayasamín', 'oswaldo guayasamin',
                    'joaquín torres garcía', 'joaquin torres garcia', 'wilfredo lam',
                    'remedios varo', 'leonora carrington'
                ],
                'palabras': [
                    'pintor', 'pintora', 'artista plástico', 'artista plastico',
                    'artista visual', 'obra pictórica', 'obra pictorica', 'cuadro',
                    'lienzo', 'óleo', 'oleo', 'acuarela', 'mural', 'muralista',
                    'retrato', 'paisaje', 'bodegón', 'bodegon', 'arte plástico',
                    'arte plastico', 'pintura', 'exposición', 'exposicion', 'galería',
                    'galeria', 'museo de arte', 'colección', 'coleccion', 'estilo pictórico',
                    'estilo pictorico', 'movimiento artístico', 'movimiento artistico',
                    'painter', 'artist', 'artwork', 'painting', 'canvas', 'exhibition',
                    'gallery', 'art museum', 'artistic movement', 'painted', 'drew'
                ]
            },
            'dances': {
                'entidades': [
                    'tango', 'salsa', 'cumbia', 'bachata', 'merengue', 'samba', 'bossa nova',
                    'folklore', 'folclore', 'cueca', 'marinera', 'joropo', 'chacarera',
                    'zamba', 'huayno', 'huaino', 'son', 'danzón', 'danzon', 'bolero',
                    'baile', 'danza'
                ],
                'palabras': [
                    'danza', 'baile', 'danzar', 'bailar', 'coreografía', 'coreografia',
                    'danza tradicional', 'baile tradicional', 'danza folclórica',
                    'danza folclorica', 'baile folklórico', 'baile folklorico',
                    'folklore', 'folclore', 'danza popular', 'baile popular',
                    'ritmo', 'música de baile', 'musica de baile', 'danza latinoamericana',
                    'baile latinoamericano', 'coreógrafo', 'coreografo', 'bailarín', 'bailarin',
                    'bailarina', 'compañía de danza', 'compania de danza', 'género de danza',
                    'genero de danza', 'estilo de baile', 'tradición de danza',
                    'tradicion de danza', 'dance', 'dancing', 'choreography', 'traditional dance',
                    'folk dance', 'dancer', 'dance style', 'dance genre', 'ballroom'
                ]
            },
            'movies': {
                'entidades': [
                    'casino royale', 'iron man', 'moonraker', 'spy game', 'grindhouse',
                    'planet terror', 'cantata de chile', 'acta general de chile',
                    'the abcs of death', 'algo habrán hecho'
                ],
                'palabras': [
                    'película', 'pelicula', 'film', 'cine', 'cinematografía', 'cinematografia',
                    'director de fotografía', 'director de fotografia', 'miembro del reparto',
                    'cast member', 'actor', 'actriz', 'género cinematográfico',
                    'genero cinematografico', 'idioma de la película', 'idioma de la pelicula',
                    'programa de televisión', 'programa de television', 'serie', 'episodio',
                    'emisora', 'original broadcaster', 'estreno', 'premiere', 'productor',
                    'producer', 'guion', 'guión', 'screenplay', 'screenwriter', 'director',
                    'film director', 'movie', 'cinema', 'box office', 'filming',
                    'producción cinematográfica', 'produccion cinematografica',
                    'industria del cine', 'cine de', 'género de', 'genero de',
                    'distribuidor', 'distribución', 'distribucion'
                ]
            },
            'other': {
                'entidades': [],
                'palabras': [
                    'propiedad', 'wikidata', 'identificador', 'restricción', 'restriccion',
                    'ejemplo', 'categoría en commons', 'categoria en commons', 'valor',
                    'formato', 'subclass', 'instance of', 'political', 'político', 'politico',
                    'guerra', 'batalla', 'organización', 'organizacion', 'institución',
                    'institucion', 'ministerio', 'partido', 'elecciones'
                ]
            }
        }
        
    def normalize_text(self, text: str) -> str:
        """Normaliza texto para comparación (minúsculas, sin acentos extra)"""
        if not text:
            return ""
        text = text.lower().strip()
        # Simplificar algunos caracteres especiales comunes
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    def detect_category(self, entidad: str, preguntas: List[Dict]) -> str:
        """
        Detecta la categoría basándose en la entidad y las preguntas
        
        Args:
            entidad: Nombre de la entidad
            preguntas: Lista de preguntas asociadas
            
        Returns:
            Categoría detectada
        """
        entidad_norm = self.normalize_text(entidad)
        
        # Combinar todo el texto de las preguntas para análisis
        texto_completo = entidad_norm + " "
        for p in preguntas:
            texto_completo += self.normalize_text(p.get('pregunta', '')) + " "
            texto_completo += self.normalize_text(p.get('respuesta_correcta', '')) + " "
        
        # Contar coincidencias para cada categoría
        scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            
            # Puntos por coincidencia en entidad
            for keyword in keywords['entidades']:
                keyword_norm = self.normalize_text(keyword)
                if keyword_norm in entidad_norm:
                    score += 5  # Mayor peso a coincidencias en entidad
                    
            # Puntos por coincidencia en preguntas
            for keyword in keywords['palabras']:
                keyword_norm = self.normalize_text(keyword)
                if keyword_norm in texto_completo:
                    score += texto_completo.count(keyword_norm)
                    
            scores[category] = score
        
        # Reglas especiales para desambiguar y priorizar categorías específicas
        
        # Prioridad 1: Pueblos Indígenas (máxima prioridad)
        if scores.get('indigenous_peoples', 0) > 0:
            scores['indigenous_peoples'] += 10  # Boost significativo
        
        # Prioridad 2: Danzas
        if scores.get('dances', 0) > 0:
            scores['dances'] += 8
        
        # Prioridad 3: Pintores
        if scores.get('painters', 0) > 0:
            scores['painters'] += 7
        
        # Prioridad 4: Películas
        if scores.get('movies', 0) > 0:
            scores['movies'] += 5
        
        # Si hay conflicto entre landmarks y otras categorías específicas
        if scores.get('landmarks', 0) > 0:
            # Landmarks tiene menor prioridad que las categorías específicas
            for specific_cat in ['indigenous_peoples', 'dances', 'painters', 'movies']:
                if scores.get(specific_cat, 0) > 0:
                    scores['landmarks'] = max(0, scores['landmarks'] - 3)
        
        # Encontrar categoría con mayor score
        if max(scores.values()) == 0:
            return 'other'
        
        return max(scores, key=scores.get)
    
    def categorize_dataset(self, input_file: str, output_file: str):
        """
        Procesa el dataset completo y agrega categorías
        
        Args:
            input_file: Ruta al archivo JSON de entrada
            output_file: Ruta al archivo JSON de salida
        """
        print(f"Leyendo dataset desde {input_file}...")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Estadísticas
        stats = Counter()
        total_entities = 0
        
        # Procesar cada región
        for region_key in data:
            if isinstance(data[region_key], list):
                print(f"\nProcesando región: {region_key}")
                
                for item in data[region_key]:
                    entidad = item.get('entidad', '')
                    preguntas = item.get('preguntas', [])
                    
                    # Detectar categoría
                    category = self.detect_category(entidad, preguntas)
                    
                    # Agregar categoría al item
                    item['category'] = category
                    
                    # Actualizar estadísticas
                    stats[category] += 1
                    total_entities += 1
                    
                    if total_entities % 100 == 0:
                        print(f"  Procesadas {total_entities} entidades...")
        
        # Guardar resultado
        print(f"\nGuardando dataset categorizado en {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        # Mostrar estadísticas
        print("\n" + "="*60)
        print("RESUMEN DE CATEGORIZACIÓN")
        print("="*60)
        print(f"Total de entidades procesadas: {total_entities}")
        print("\nDistribución por categorías:")
        for category, count in stats.most_common():
            percentage = (count / total_entities) * 100
            print(f"  {category:20s}: {count:6d} ({percentage:5.2f}%)")
        print("="*60)
        
        return stats


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Categorizar automáticamente entradas del dataset'
    )
    parser.add_argument(
        'input_file',
        nargs='?',
        default='subset_experimento_final.json',
        help='Archivo JSON de entrada (default: subset_experimento_final.json)'
    )
    parser.add_argument(
        'output_file',
        nargs='?',
        default='subset_experimento_categorizado.json',
        help='Archivo JSON de salida (default: subset_experimento_categorizado.json)'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Modo interactivo para revisar y ajustar categorías'
    )
    
    args = parser.parse_args()
    
    categorizer = DatasetCategorizer()
    stats = categorizer.categorize_dataset(args.input_file, args.output_file)
    
    print("\n✓ Categorización completada exitosamente!")
    print(f"✓ Archivo generado: {args.output_file}")


if __name__ == '__main__':
    main()
