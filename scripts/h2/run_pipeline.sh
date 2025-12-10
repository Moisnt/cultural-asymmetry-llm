#!/bin/bash

# ===================================================================================
# SCRIPT PARA EJECUTAR EL PIPELINE COMPLETO DE ANÁLISIS Y EVALUACIÓN DE MODELOS
#
# Se ejecutarán los siguientes pasos de forma secuencial:
# 1. Análisis de Trayectorias: Se analizan los logits internos para Llama3 y Qwen3.
# 2. Combinación de Trayectorias: Se unifican los resultados y se genera un gráfico comparativo.
# 3. Evaluación con Juez: Se generan respuestas y se evalúan con un modelo juez para Llama3 y Qwen3.
# 4. Combinación de Evaluaciones: Se unifican las métricas y predicciones de la evaluación.
#
# ===================================================================================

# --- Configuración de Entorno ---
# Exportar token de Hugging Face explícitamente
export HUGGING_FACE_TOKEN=""

# Asegurar que las librerías de CUDA/cuDNN sean visibles
export LD_LIBRARY_PATH=/usr/lib/python3/dist-packages/torch/lib:$LD_LIBRARY_PATH

# --- Configuración ---
GPUS=(0 1 2 3 4 5 6 7) # GPUs a utilizar
MODELOS=("llama3" "qwen3") # Modelos a procesar
NUM_GPUS=${#GPUS[@]}
BASE_DIR="/workspace1/gonzalo.fuentes/proyecto_generativa/h2"
cd "$BASE_DIR" || exit 1
RESULTS_DIR="${BASE_DIR}/resultados_h2"

# Crear directorio de resultados si no existe
mkdir -p ${RESULTS_DIR}

# ===================================================================================
# PASO 1: ANÁLISIS DE TRAYECTORIAS (PARALELO)
# ===================================================================================
echo "PASO 1: Iniciando análisis de trayectorias para los modelos: ${MODELOS[*]}..."

for modelo in ${MODELOS[@]}; do
    echo "  -> Lanzando análisis para el modelo: $modelo en GPUs ${GPUS[*]}"
    for i in $(seq 0 $(($NUM_GPUS - 1))); do
        GPU_ID=${GPUS[$i]}
        python3 ${BASE_DIR}/1_analizar_trayectorias_paralelo.py \
            --model_name ${modelo} \
            --gpu_id ${GPU_ID} \
            --partition ${i} \
            --total_partitions ${NUM_GPUS} \
            --results_dir ${RESULTS_DIR} &
    done
    wait
    echo "  -> Análisis para $modelo completado."
done

echo "PASO 1 completado."
echo "==================================================================================="


# ===================================================================================
# PASO 2: COMBINAR RESULTADOS DE TRAYECTORIAS Y GENERAR GRÁFICO
# ===================================================================================
echo "PASO 2: Combinando trayectorias y generando gráfico comparativo..."
python3 ${BASE_DIR}/2_combinar_y_graficar.py --results_dir ${RESULTS_DIR}
echo "PASO 2 completado."
echo "==================================================================================="


# ===================================================================================
# PASO 3: EVALUACIÓN CON JUEZ (PARALELO)
# ===================================================================================
echo "PASO 3: Iniciando evaluación con juez para los modelos: ${MODELOS[*]}..."

for modelo in ${MODELOS[@]}; do
    echo "  -> Lanzando evaluación para el modelo: $modelo en GPUs ${GPUS[*]}"
    for i in $(seq 0 $(($NUM_GPUS - 1))); do
        GPU_ID=${GPUS[$i]}
        python3 ${BASE_DIR}/3_evaluar_paralelo.py \
            --model_name ${modelo} \
            --gpu_id ${GPU_ID} \
            --partition ${i} \
            --total_partitions ${NUM_GPUS} \
            --results_dir ${RESULTS_DIR} &
    done
    wait
    echo "  -> Evaluación para $modelo completada."
done

echo "PASO 3 completado."
echo "==================================================================================="


# ===================================================================================
# PASO 4: COMBINAR RESULTADOS DE EVALUACIÓN
# ===================================================================================
echo "PASO 4: Combinando resultados finales de la evaluación..."
python3 ${BASE_DIR}/4_combinar_resultados.py --total_partitions ${NUM_GPUS} --results_dir ${RESULTS_DIR}
echo "PASO 4 completado."
echo "==================================================================================="

echo "¡PIPELINE COMPLETO!"
echo "Todos los análisis y evaluaciones han finalizado."
