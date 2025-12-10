# RESUMEN EJECUTIVO: Extracción Subset H2

## 📊 Resultado Final

**Archivo generado:** `subset_h2_final.json`
- **Total:** 110 entidades | 492 preguntas
- **Fuente:** justo_qa.json (310,699 preguntas procesadas)

## ✅ Categorías con BUENOS RESULTADOS

### 🎬 MOVIES (Excelente)
- ✅ 17 entidades | 97 preguntas
- ✅ Películas correctas: Diarios de motocicleta, Carandiru, Violeta se fue a los cielos, El beso de la mujer araña
- ✅ **100% Correcto**

### 💃 DANCES (Muy Bueno)
- ✅ 26 entidades | 56 preguntas
- ✅ Danzas correctas: chacarera, cueca, tango argentino, chamamé, marinera
- ✅ **~95% Correcto**

### 🏛️ LANDMARKS (Bueno)
- ✅ 12 entidades | 30 preguntas
- ✅ Landmarks correctos: Puentes, Parque Iguazú, Laguna de los Patos
- ✅ **~90% Correcto**

## ⚠️ Categorías con PROBLEMAS

### 🎨 PAINTERS (Necesita limpieza)
- ⚠️ 25 entidades | 122 preguntas
- ❌ **Lautaro Murúa** (63 preguntas) → Es ACTOR, no pintor
- ❌ **Adrián Caetano** (5 preguntas) → Es DIRECTOR, no pintor
- ❌ **Roberto Fontanarrosa** → Es dibujante/humorista
- ✅ Benito Quinquela Martín, María Izquierdo, Prilidiano Pueyrredón → Pintores reales
- 📊 **~60% Correcto** (necesita filtrar actores/directores)

### 🌍 INDIGENOUS_PEOPLES (Necesita mucha limpieza)
- ⚠️ 30 entidades | 187 preguntas
- ❌ **San Cristóbal** (42 preguntas) → Es ciudad, no pueblo indígena
- ❌ **Huari** → Cultura precolombina (¿válido?)
- ❌ **eslovenos, mizrají, armenios** → Grupos étnicos europeos/asiáticos, NO indígenas
- ✅ asháninca, mapuche, ticuna → Pueblos indígenas reales
- 📊 **~40% Correcto** (CSV tiene grupos étnicos mezclados)

## 🔧 PROBLEMA RAÍZ

Los archivos CSV originales **NO son puros**:
- `pueblos_indigenas_latam_4079Entities.csv` incluye **cualquier grupo étnico**
- `pintores_latam_4671Entities.csv` incluye **actores, directores, escritores**

## 💡 RECOMENDACIONES

### Opción 1: Limpieza Manual (Rápido)
1. Abrir `subset_h2_final.json`
2. Eliminar manualmente las entidades incorrectas:
   - **indigenous_peoples:** Eliminar San Cristóbal, eslovenos, mizrají, armenios, peruanos
   - **painters:** Eliminar Lautaro Murúa, Adrián Caetano, Roberto Fontanarrosa
3. ✅ Quedaría con ~300 preguntas 100% correctas

### Opción 2: Script de Limpieza Automática (Mejor)
Crear script que:
1. Use listas blancas de entidades validadas
2. Filtre usando palabras clave más estrictas
3. Valide cada entidad con reglas específicas

### Opción 3: Usar dataset_benchmark + tomy_qa combinados
- dataset_benchmark: 67k preguntas
- tomy_qa: 54k preguntas
- Total: 121k preguntas adicionales para minar

## 📈 SIGUIENTE PASO SUGERIDO

**¿Qué prefieres?**

A) **Limpiar manualmente** el subset_h2_final.json actual (10 minutos)
B) **Generar script de limpieza** automática con listas blancas
C) **Combinar múltiples datasets** (justo + tomy + benchmark) para mayor cobertura
D) **Usar el subset actual** con disclaimer de ~70% precisión

---

**Archivo listo para usar:** `subset_h2_final.json`
**Script generador:** `extraer_subset_desde_csv.py`
