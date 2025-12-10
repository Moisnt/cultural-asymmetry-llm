import warnings
warnings.filterwarnings("ignore")
import os
from glob import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse

# --- Configuración de Estilo ---
plt.style.use('seaborn-whitegrid')

# --- Funciones Principales ---

def combinar_trayectorias(results_dir, model_name):
    """
    Encuentra y combina todos los archivos de trayectoria de un directorio para un modelo específico.
    """
    search_path = os.path.join(results_dir, f'trayectorias_{model_name}_part_*.csv')
    trajectory_files = sorted(glob(search_path))
    
    if not trajectory_files:
        print(f"Advertencia: No se encontraron archivos de trayectoria en '{results_dir}' para el modelo '{model_name}'.")
        return pd.DataFrame()
        
    print(f"Archivos de trayectoria encontrados para '{model_name}': {trajectory_files}")
    
    all_trajectories_df = pd.concat((pd.read_csv(f) for f in trajectory_files), ignore_index=True)
    return all_trajectories_df

def procesar_y_guardar_promedios(df_trajectories, results_dir, model_name):
    """
    Calcula las probabilidades promedio por capa y categoría y guarda el resultado.
    """
    if df_trajectories.empty:
        return pd.DataFrame()
        
    # --- CORRECCIÓN: Especificar las columnas numéricas para promediar ---
    numeric_cols = ['ground_truth_prob', 'top_1_prob']
    
    # Usar 'category' si existe, sino fallback a 'region'
    group_col = 'category' if 'category' in df_trajectories.columns else 'region'
    
    avg_probs = df_trajectories.groupby(['layer', group_col])[numeric_cols].mean().reset_index()
    # -------------------------------------------------------------------
    
    output_avg_csv_path = os.path.join(results_dir, f'trayectorias_promedio_{model_name}.csv')
    avg_probs.to_csv(output_avg_csv_path, index=False)
    print(f"Datos con promedios para '{model_name}' guardados en: {output_avg_csv_path}")
    
    return avg_probs

import numpy as np

def generar_grafico(avg_probs, results_dir, model_name=""):
    """
    Genera y guarda el gráfico de líneas con Matplotlib para manejar múltiples categorías.
    """
    fig, ax = plt.subplots(figsize=(15, 8))
    
    group_col = 'category' if 'category' in avg_probs.columns else 'region'
    
    # Obtener categorías únicas y asignar colores
    categories = sorted(avg_probs[group_col].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, len(categories)))
    
    for i, cat in enumerate(categories):
        subset = avg_probs[avg_probs[group_col] == cat].sort_values('layer')
        ax.plot(subset['layer'].values, subset['ground_truth_prob'].values, 
                label=cat, color=colors[i], marker='o', linestyle='-', linewidth=2)
    
    ax.set_title(f'Probabilidad Promedio de Ground Truth por Capa ({model_name})', fontsize=16)
    ax.set_xlabel('Capa del Modelo', fontsize=12)
    ax.set_ylabel('Probabilidad Promedio', fontsize=12)
    ax.legend(title=group_col.capitalize(), bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    output_image_path = os.path.join(results_dir, f'trayectorias_probabilidad_{model_name}.png')
    plt.savefig(output_image_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráfico guardado en: {output_image_path}")

def generar_grafico_top1(avg_probs, results_dir, model_name=""):
    """
    Genera y guarda el gráfico de líneas para Top-1 Probability.
    """
    fig, ax = plt.subplots(figsize=(15, 8))
    
    group_col = 'category' if 'category' in avg_probs.columns else 'region'
    
    # Obtener categorías únicas y asignar colores
    categories = sorted(avg_probs[group_col].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, len(categories)))
    
    for i, cat in enumerate(categories):
        subset = avg_probs[avg_probs[group_col] == cat].sort_values('layer')
        ax.plot(subset['layer'].values, subset['top_1_prob'].values, 
                label=cat, color=colors[i], marker='x', linestyle='--', linewidth=2)
    
    ax.set_title(f'Probabilidad Promedio Top-1 por Capa ({model_name})', fontsize=16)
    ax.set_xlabel('Capa del Modelo', fontsize=12)
    ax.set_ylabel('Probabilidad Promedio (Top-1)', fontsize=12)
    ax.legend(title=group_col.capitalize(), bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    output_image_path = os.path.join(results_dir, f'trayectorias_probabilidad_top1_{model_name}.png')
    plt.savefig(output_image_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráfico Top-1 guardado en: {output_image_path}")

def generar_grafico_ground_truth(avg_probs, results_dir, model_name=""):
    # Esta función es redundante con la nueva implementación genérica, 
    # pero la mantenemos por compatibilidad si se llama desde main
    pass

def generar_strip_heatmap(avg_probs, results_dir):
    """
    Genera un heatmap de 2 filas (LATAM/USA) x 32 columnas (capas) para
    visualizar la probabilidad promedio de Ground Truth.
    """
    try:
        # Pivotear la tabla para que las regiones sean filas y las capas columnas
        heatmap_data = avg_probs.pivot(index='region', columns='layer', values='ground_truth_prob')
        
        # Asegurar el orden deseado de las filas
        heatmap_data = heatmap_data.reindex(['latam', 'usa'])

        plt.figure(figsize=(20, 3)) # Gráfico ancho y de poca altura
        ax = sns.heatmap(
            heatmap_data,
            vmin=0,
            vmax=0.4, # Fijar un máximo para consistencia entre modelos, o usar heatmap_data.max().max()
            cmap='viridis',
            annot=False, # No anotar los valores numéricos
            linewidths=.5,
            cbar_kws={'label': 'Probabilidad Promedio (Ground Truth)'}
        )

        ax.set_title('Probabilidad Promedio de Ground Truth por Capa (LATAM vs. USA)', fontsize=16)
        ax.set_xlabel('Capa del Modelo', fontsize=12)
        ax.set_ylabel('Región', fontsize=12)
        ax.set_yticklabels(['LATAM', 'USA'], rotation=0, ha='right') # Renombrar y alinear etiquetas

        output_image_path = os.path.join(results_dir, 'strip_heatmap_promedios.png')
        plt.savefig(output_image_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Strip Heatmap guardado en: {output_image_path}")

    except Exception as e:
        print(f"No se pudo generar el Strip Heatmap de Ground Truth: {e}")

def generar_strip_heatmap_top1(avg_probs, results_dir):
    """
    Genera un heatmap de 2 filas (LATAM/USA) x 32 columnas (capas) para
    visualizar la probabilidad promedio de Top-1.
    """
    try:
        heatmap_data = avg_probs.pivot(index='region', columns='layer', values='top_1_prob')
        heatmap_data = heatmap_data.reindex(['latam', 'usa'])

        plt.figure(figsize=(20, 3))
        ax = sns.heatmap(
            heatmap_data,
            vmin=0,
            vmax=0.4,
            cmap='viridis', # Usar el mismo colormap para consistencia
            annot=False,
            linewidths=.5,
            cbar_kws={'label': 'Probabilidad Promedio (Top-1)'}
        )

        ax.set_title('Probabilidad Promedio de Top-1 por Capa (LATAM vs. USA)', fontsize=16)
        ax.set_xlabel('Capa del Modelo', fontsize=12)
        ax.set_ylabel('Región', fontsize=12)
        ax.set_yticklabels(['LATAM', 'USA'], rotation=0, ha='right')

        output_image_path = os.path.join(results_dir, 'strip_heatmap_top1_promedios.png')
        plt.savefig(output_image_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Strip Heatmap de Top-1 guardado en: {output_image_path}")

    except Exception as e:
        print(f"No se pudo generar el Strip Heatmap de Top-1: {e}")

def plot_lines_latam_vs_usa(avg_probs, results_dir, model_name):
    """
    Genera un gráfico de líneas comparando LATAM vs USA para un modelo específico.
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    # Filtrar datos por región
    df_latam = avg_probs[avg_probs['region'] == 'latam'].sort_values('layer')
    df_usa = avg_probs[avg_probs['region'] == 'usa'].sort_values('layer')

    # Colores y Estilos
    color_latam = '#1f77b4' # Azul
    color_usa = '#ff7f0e'   # Naranja
    
    # Graficar LATAM
    if not df_latam.empty:
        ax.plot(df_latam['layer'].to_numpy(), df_latam['ground_truth_prob'].to_numpy(), 
                label='LATAM (Ground Truth)', color=color_latam, linestyle='-', marker='o', linewidth=2)
        ax.plot(df_latam['layer'].to_numpy(), df_latam['top_1_prob'].to_numpy(), 
                label='LATAM (Top-1)', color=color_latam, linestyle='--', marker='x', alpha=0.7)

    # Graficar USA
    if not df_usa.empty:
        ax.plot(df_usa['layer'].to_numpy(), df_usa['ground_truth_prob'].to_numpy(), 
                label='USA (Ground Truth)', color=color_usa, linestyle='-', marker='o', linewidth=2)
        ax.plot(df_usa['layer'].to_numpy(), df_usa['top_1_prob'].to_numpy(), 
                label='USA (Top-1)', color=color_usa, linestyle='--', marker='x', alpha=0.7)

    ax.set_title(f'Trayectorias de Probabilidad: {model_name} (LATAM vs USA)', fontsize=18, pad=15)
    ax.set_xlabel('Capa del Modelo', fontsize=14)
    ax.set_ylabel('Probabilidad Promedio', fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    
    output_path = os.path.join(results_dir, f'grafico_lineas_{model_name}_latam_vs_usa.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráfico de líneas guardado en: {output_path}")

def generar_heatmap_categorias(avg_probs, results_dir, model_name, metric='ground_truth_prob'):
    """
    Genera un heatmap para visualizar la probabilidad promedio por categoría y capa.
    """
    group_col = 'category' if 'category' in avg_probs.columns else 'region'
    
    # Pivotear datos: Filas=Categoría, Columnas=Capa
    heatmap_data = avg_probs.pivot(index=group_col, columns='layer', values=metric)
    
    # Ordenar filas alfabéticamente
    heatmap_data = heatmap_data.sort_index()

    plt.figure(figsize=(20, len(heatmap_data) * 0.8 + 2)) # Altura dinámica según número de categorías
    ax = sns.heatmap(
        heatmap_data,
        cmap='viridis',
        annot=False,
        linewidths=0.5,
        cbar_kws={'label': 'Probabilidad'}
    )
    
    metric_label = "Top-1" if metric == 'top_1_prob' else "Ground Truth"
    ax.set_title(f'Mapa de Calor {metric_label}: {model_name}', fontsize=16, pad=10)
    ax.set_xlabel('Capa del Modelo', fontsize=12)
    ax.set_ylabel(group_col.capitalize(), fontsize=12)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

    output_path = os.path.join(results_dir, f'grafico_heatmap_{model_name}_{metric}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Heatmap ({metric}) guardado en: {output_path}")

def generar_graficos_modelo(avg_probs, results_dir, model_name):
    """
    Genera todos los gráficos solicitados para un modelo.
    """
    print(f"\nGenerando gráficos para {model_name}...")
    
    # Gráfico de líneas Ground Truth
    generar_grafico(avg_probs, results_dir, model_name)
    
    # Gráfico de líneas Top-1
    generar_grafico_top1(avg_probs, results_dir, model_name)
    
    # Heatmaps
    generar_heatmap_categorias(avg_probs, results_dir, model_name, metric='ground_truth_prob')
    generar_heatmap_categorias(avg_probs, results_dir, model_name, metric='top_1_prob')

def plot_comparative_models_ground_truth(avg_probs_dict, results_dir):
    """
    Genera un gráfico comparativo de Ground Truth para múltiples modelos y categorías.
    """
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Estilos de línea para diferenciar modelos
    line_styles = ['-', '--', '-.', ':']
    model_styles = {model: line_styles[i % len(line_styles)] for i, model in enumerate(avg_probs_dict.keys())}
    
    # Recolectar todas las categorías para asignar colores consistentes
    all_cats = set()
    for df in avg_probs_dict.values():
        if not df.empty:
            group_col = 'category' if 'category' in df.columns else 'region'
            all_cats.update(df[group_col].unique())
    
    # Crear paleta de colores
    sorted_cats = sorted(list(all_cats))
    colors = plt.cm.tab10(np.linspace(0, 1, len(sorted_cats)))
    cat_colors = {cat: colors[i] for i, cat in enumerate(sorted_cats)}

    for model_name, avg_probs in avg_probs_dict.items():
        if avg_probs.empty:
            continue
            
        group_col = 'category' if 'category' in avg_probs.columns else 'region'
        
        for cat in avg_probs[group_col].unique():
            subset = avg_probs[avg_probs[group_col] == cat].sort_values('layer')
            ax.plot(subset['layer'].values, subset['ground_truth_prob'].values,
                    label=f"{model_name} - {cat}",
                    color=cat_colors.get(cat, 'black'),
                    linestyle=model_styles.get(model_name, '-'),
                    marker='o', markersize=4)

    ax.set_title('Comparación de Modelos: Probabilidad Ground Truth por Categoría', fontsize=18, pad=15)
    ax.set_xlabel('Capa del Modelo', fontsize=14)
    ax.set_ylabel('Probabilidad Promedio (Ground Truth)', fontsize=14)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.6)
    
    output_path = os.path.join(results_dir, 'grafico_comparativo_modelos_ground_truth.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráfico comparativo de modelos guardado en: {output_path}")

def plot_comparative_models_top1(avg_probs_dict, results_dir):
    """
    Genera un gráfico comparativo de Top-1 para múltiples modelos y categorías.
    """
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Estilos de línea para diferenciar modelos
    line_styles = ['-', '--', '-.', ':']
    model_styles = {model: line_styles[i % len(line_styles)] for i, model in enumerate(avg_probs_dict.keys())}
    
    # Recolectar todas las categorías para asignar colores consistentes
    all_cats = set()
    for df in avg_probs_dict.values():
        if not df.empty:
            group_col = 'category' if 'category' in df.columns else 'region'
            all_cats.update(df[group_col].unique())
    
    # Crear paleta de colores
    sorted_cats = sorted(list(all_cats))
    colors = plt.cm.tab10(np.linspace(0, 1, len(sorted_cats)))
    cat_colors = {cat: colors[i] for i, cat in enumerate(sorted_cats)}

    for model_name, avg_probs in avg_probs_dict.items():
        if avg_probs.empty:
            continue
            
        group_col = 'category' if 'category' in avg_probs.columns else 'region'
        
        for cat in avg_probs[group_col].unique():
            subset = avg_probs[avg_probs[group_col] == cat].sort_values('layer')
            ax.plot(subset['layer'].values, subset['top_1_prob'].values,
                    label=f"{model_name} - {cat}",
                    color=cat_colors.get(cat, 'black'),
                    linestyle=model_styles.get(model_name, '-'),
                    marker='x', markersize=4)

    ax.set_title('Comparación de Modelos: Probabilidad Top-1 por Categoría', fontsize=18, pad=15)
    ax.set_xlabel('Capa del Modelo', fontsize=14)
    ax.set_ylabel('Probabilidad Promedio (Top-1)', fontsize=14)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.6)
    
    output_path = os.path.join(results_dir, 'grafico_comparativo_modelos_top1.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráfico comparativo de modelos Top-1 guardado en: {output_path}")

# --- Bloque de Ejecución ---

def main():
    parser = argparse.ArgumentParser(description="Combinar trayectorias y graficar.")
    parser.add_argument("--results_dir", type=str, default="resultados", help="Directorio donde leer/guardar los resultados.")
    args = parser.parse_args()

    results_dir = args.results_dir
    modelos = ['llama3', 'qwen3'] 
    
    avg_probs_dict = {}

    for model in modelos:
        print(f"--- Procesando modelo: {model} ---")
        df_trajectories = combinar_trayectorias(results_dir, model)
        
        if not df_trajectories.empty:
            # Calcular promedios
            avg_probs = procesar_y_guardar_promedios(df_trajectories, results_dir, model)
            avg_probs_dict[model] = avg_probs
            
            # Generar gráficos individuales
            generar_graficos_modelo(avg_probs, results_dir, model)
        else:
            print(f"No se encontraron datos para '{model}'. Saltando gráficos.")
            
    # Generar gráfico comparativo global si hay datos
    if avg_probs_dict:
        print("\nGenerando gráficos comparativos globales...")
        plot_comparative_models_ground_truth(avg_probs_dict, results_dir)
        plot_comparative_models_top1(avg_probs_dict, results_dir)

if __name__ == "__main__":
    main()
