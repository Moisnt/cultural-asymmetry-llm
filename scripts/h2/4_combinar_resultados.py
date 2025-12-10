import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import os
import argparse

def combine_model_results(model_name, total_partitions, results_dir):
    # Lista para almacenar los DataFrames de cada partición
    all_partitions = []
    
    print(f"--- Combinando resultados para el modelo: {model_name} ---")
    for i in range(total_partitions):
        file_path = os.path.join(results_dir, f'predicciones_{model_name}_part_{i}.csv')
        if os.path.exists(file_path):
            print(f"Leyendo '{file_path}'...")
            df_part = pd.read_csv(file_path)
            all_partitions.append(df_part)
        else:
            print(f"ADVERTENCIA: No se encontró el archivo de resultados '{file_path}'.")
            
    if not all_partitions:
        print(f"No se encontraron archivos de resultados para el modelo '{model_name}'.")
        return

    # Combinar todos los DataFrames en uno solo
    df_combined = pd.concat(all_partitions, ignore_index=True)

    # 1. Guardar el archivo completo con todas las predicciones
    full_path = os.path.join(results_dir, f'predicciones_completas_{model_name}.csv')
    df_combined.to_csv(full_path, index=False)
    print(f"\nArchivo combinado para '{model_name}' guardado en '{full_path}'")

    # 2. Calcular y guardar las métricas promedio por categoría
    if 'category' in df_combined.columns:
        avg_metrics = df_combined.groupby('category')[['f1_score', 'substring_accuracy', 'judge_score']].mean()
        print(f"\nResultados de Evaluación para '{model_name}' (Promedio por Categoría):")
    elif 'region' in df_combined.columns:
        # Fallback por si acaso
        avg_metrics = df_combined.groupby('region')[['f1_score', 'substring_accuracy', 'judge_score']].mean()
        print(f"\nResultados de Evaluación para '{model_name}' (Promedio por Región):")
    else:
        print("No se encontró columna de agrupación (category/region).")
        return

    avg_path = os.path.join(results_dir, f'metricas_promedio_{model_name}.csv')
    avg_metrics.to_csv(avg_path)
    
    print(avg_metrics)
    print(f"Métricas promedio para '{model_name}' guardadas en '{avg_path}'")

def main():
    parser = argparse.ArgumentParser(description="Combinar resultados de la evaluación paralela para múltiples modelos.")
    parser.add_argument("--total_partitions", type=int, required=True, help="Número total de particiones que se ejecutaron.")
    parser.add_argument("--results_dir", type=str, default="resultados", help="Directorio donde leer/guardar los resultados.")
    args = parser.parse_args()
    
    modelos = ['llama3', 'qwen3'] # Modelos a procesar

    for model in modelos:
        combine_model_results(model, args.total_partitions, args.results_dir)
        print("-" * 50)

    print("\n¡Proceso de combinación completado para todos los modelos!")

if __name__ == "__main__":
    main()
