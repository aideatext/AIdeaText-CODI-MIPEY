# Sesión pendiente — plan de progresión de complejidad

> **Concepto.** Quien dona no le invita un café a AIdeaText: le invita **una sesión de tutor a un estudiante que no conoce**.
> El estudiante recibe el valor primero. El subproducto es su progreso medido (M1 Coherencia Dialógica, M2 Robustez Estructural),
> que le sirve como **constancia de aprendizaje portable**. Al donante se le muestra el **impacto agregado**, nunca la identidad del estudiante.

## Principio de diseño: anonimato ≠ blockchain

Son dos propiedades distintas y se resuelven con herramientas distintas:

| Propiedad | Qué garantiza | Cómo se logra |
|---|---|---|
| **Anonimato** | El donante no sabe quién recibió; el estudiante no sabe quién donó | **Fondo común** (las donaciones se mezclan antes de asignarse) + **agregación** (nunca reportar grupos de menos de *k* estudiantes) |
| **Verificabilidad** | El donante puede comprobar que su donación entró y se usó, sin confiar a ciegas en AIdeaText | **Registro inmutable**: cadena de hashes → árbol de Merkle publicado → (opcional) anclaje en blockchain |

Así funcionan las organizaciones de patrocinio tipo World Vision: el anonimato lo da el **fondo intermediario**, no la tecnología.
Una blockchain pública es **seudónima, no anónima**: escribir en ella datos de estudiantes los expondría para siempre.
Por eso **nunca va un dato personal en cadena**; solo compromisos criptográficos (hashes).

Cada nivel funciona por sí solo (pasa el test de Raíz: *funciona si AIdeaText es el primero y el único en adoptarlo*) y el siguiente se monta encima.

---

## Nivel 0 — Fondo común visible · *hackathon, hoy*

**Qué hace:** el "café" se convierte en "sesiones pendientes". Precio de referencia: 1 sesión = $10 MXN (configurable).

- QR CoDi de monto libre → la donación entra al **fondo**; el muro muestra *"$X donados = N sesiones pendientes · M ya usadas"*.
- Cada donación recibe un **folio de donante** (no requiere cuenta ni datos personales).
- Sin vínculo entre donación y estudiante.

**Cambios técnicos:** tabla `fondo_movimientos` (entradas por donación); `/cafe` muestra sesiones financiadas.
**Demuestra:** CoDi sin comisión + observabilidad (Rogers) + bien público.

## Nivel 1 — Asignación y canje · *semanas 1–2*

**Qué hace:** los estudiantes del piloto consumen sesiones del fondo; el donante ve el estado de su aporte.

- **Libro de doble entrada**: `donación → fondo → asignación → sesión consumida`. Las asignaciones salen del fondo (FIFO), no de una donación concreta → anonimato por mezcla.
- **Folio de donante** consultable: `en fondo / asignada / usada` + impacto agregado.
- **Impacto agregado con umbral k ≥ 5**: sesiones usadas, promedio de M1/M2, solo por cohorte; nunca individuos.
- Reglas de elegibilidad del estudiante (inscrito en piloto, institución aliada) — sin pedir datos económicos.

**Cambios técnicos:** `store.py` → libro contable; descuento de crédito al iniciar sesión del tutor; endpoint `/impacto`.
**Demuestra:** el estudiante recibe valor antes de dar cualquier dato (Spence / modelo Yape).

## Nivel 2 — Verificable sin blockchain · *mes 1*

**Qué hace:** nadie tiene que confiar a ciegas en AIdeaText.

- Registro **solo-anexar** con **cadena de hashes** (cada movimiento incluye el hash del anterior).
- Publicación diaria de la **raíz de Merkle** del libro (página pública + repositorio).
- El folio del donante trae su **prueba de inclusión**: puede verificar que su donación está en el libro publicado.
- **Constancia de aprendizaje** del estudiante: PDF + XML **firmados digitalmente**, con M1/M2 y número de sesiones; verificable por terceros.
  Formato objetivo: **Open Badges 3.0 / W3C Verifiable Credentials**. El estudiante la porta y decide a quién mostrarla.

**Demuestra:** transparencia auditable con infraestructura propia y costo cero.

## Nivel 3 — Anclaje en cadena pública · *meses 2–3*

**Qué hace:** la raíz de Merkle diaria se **ancla** en una blockchain pública (sello de tiempo imborrable).

- En cadena solo va un hash por día: **ningún dato personal, ningún monto individual**.
- Credenciales del estudiante con identificadores descentralizados (DID) para verificación sin AIdeaText.
- Evaluar red de bajo costo y la opción más simple (p. ej. OpenTimestamps sobre Bitcoin) antes que un contrato inteligente.

**Demuestra:** garantía de integridad independiente de AIdeaText y de cualquier gobierno.

## Nivel 4 — Exploratorio

Mecanismos de distribución más ricos y otros medios de aportación. Se definirá en su momento; requiere revisión regulatoria (Ley Fintech, Banxico) y de protección de datos de menores.

---

## Relación con el ecosistema AIdeaText

El fondo y el libro son un **servicio transversal** (`pey_payments` + libro contable) que consumen los servicios en línea (concursa queda fuera por ahora: no aplica a México).
La unidad común es el **crédito de sesión**: cada servicio define cuánto vale una sesión suya y qué señal produce.

| Servicio | Qué es | "Pendiente" que se dona | Señal que produce (subproducto) | Quién paga además |
|---|---|---|---|---|
| **conText** · context.aideatext.ai | Tutor socrático; grafo en vivo con origen de cada idea (estudiante / tutor / material) | **Sesión de tutor** (ya tiene modelo de pago por uso) | Proporción de ideas propias en el grafo | Licencia personal o corporativa por uso |
| **AIdeaText** · aideatext.ai, v61-dev, edu | Escritura y argumentación; huella del argumento como grafo; vista del profesor | **Ciclo de borrador** (borrador → retroalimentación → revisión) | M1 Coherencia Dialógica, M2 Robustez Estructural, cambio entre borradores | Institución (edu) |
| **AIDesk** · aidesk.aideatext.ai | PDF → Markdown en el navegador, diagnóstico, transcripción y traducción | **Minutos de transcripción/traducción** (hoy 1 minuto gratis) | Ninguna sobre la persona (el audio se borra al entregar) | Usuario por volumen |
| **SSA** · ssa.aideatext.ai | Simulación social con cientos de agentes (basada en MiroFish) | — (no aplica a donación individual) | — | Institucional; además puede **simular reglas de asignación del fondo** antes de aplicarlas |

Consecuencias de diseño:
- **Un solo libro, muchos destinos**: el donante elige "fondo general" o un servicio; la asignación siempre pasa por el fondo (anonimato por mezcla).
- **Constancia de aprendizaje** solo la emiten conText y AIdeaText, que son los que miden proceso; AIDesk entrega valor sin medir a la persona.
- **conText es el piloto natural**: ya tiene sesión acotada, pago por uso y borrado total → el Nivel 0–1 se prueba ahí primero.
- **Un mismo QR CoDi** sirve a todos los servicios; el destino se registra en la metadata de la orden.

## Lectura para convocatorias e investigación

- **Rogers (observabilidad):** el muro y el QR en el aula hacen visible lo que CoDi nunca hizo visible.
- **Spence / modelo Yape:** valor primero; la señal (progreso medido) es subproducto que el estudiante controla y porta.
- **Ostrom:** el fondo común necesita reglas claras, monitoreo (libro verificable) y transparencia → niveles 1–2.
- **Teoría del actor-red:** la constancia de aprendizaje convierte a AIdeaText en punto de paso obligatorio para *demostrar* aprendizaje, no para pagar.
- **Indicador de capacidades (Sen):** no "cuántos donaron", sino qué pudo hacer un estudiante que antes no podía.

## Riesgos

- **Menores de edad:** sin datos personales en reportes ni en cadena; consentimiento institucional.
- **Asignación justa:** las reglas de asignación del fondo deben ser públicas antes de operar.
- **Fiscal:** recibir donaciones como persona física o SAS no las hace deducibles para el donante (eso requiere ser donataria autorizada).
