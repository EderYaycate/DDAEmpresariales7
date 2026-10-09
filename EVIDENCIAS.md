# Evidencias — ORM con IA: duelo y verificador

Alumno: Eder Yaycate · Sección 4-C24-A · Semana 7 (extra)

> **Nota de honestidad sobre el uso de IA.** Los pasos 4 y 5 de la guía piden escribir las consultas
> «sin consultar a ninguna IA». Las respuestas de `blog/duel/team.py` y la corrección de
> `blog/queries.py` de este repositorio fueron redactadas con ayuda de un asistente de IA (Claude).
> Por eso la columna «intentos» de la tabla 2 y el diagrama dibujado a mano del paso 3 **no se
> rellenan aquí**: deben registrar lo que cada integrante hizo realmente. La tabla 7 documenta el
> uso de IA tal como ocurrió; ajústala si tu trabajo propio fue distinto.

## 1. Datos conocidos (paso 2)

Después de `python manage.py seed_blog`: **4 autores, 15 artículos, 23 comentarios** (además de
4 perfiles, 4 categorías y 5 etiquetas). De los 15 artículos, 11 están publicados y 4 son borradores.

## 2. Mis ocho consultas (pasos 4 y 5)

`python manage.py duel` → **8 de 8 correctas y baratas** (1 consulta cada una).

| Pregunta | Consulta | Verdicto | Intentos |
|---|---|---|---|
| q1 | `filter(published=True)` | ✔ correcta (1 consulta) | _por completar_ |
| q2 | `filter(category__isnull=True)` | ✔ correcta (1) | _por completar_ |
| q3 | `filter(published_at__range=(date(2026,3,1), date(2026,5,31)))` | ✔ correcta (1) | _por completar_ |
| q4 | `annotate(n_comments=Count("comments")).filter(n_comments__gt=2)` | ✔ correcta (1) | _por completar_ |
| q5 | `filter(published=True).annotate(n_comments=Count("comments", distinct=True), n_tags=Count("tags", distinct=True)).order_by("-n_comments")[:3]` | ✔ correcta (1) | _por completar_ |
| q6 | `filter(author__profile__country="Perú")` | ✔ correcta (1) | _por completar_ |
| q7 | `Comment.objects.filter(post__category__name="Tecnología")` | ✔ correcta (1) | _por completar_ |
| q8 | `Author.objects.exclude(posts__published=True)` | ✔ correcta (1) | _por completar_ |

Anotación de la q5: `n_comments` y `n_tags` de los tres artículos son (6, 3), (4, 2) y (3, 4).

## 3. Veredicto de la IA y clasificación de sus fallos (pasos 6 y 7)

`python manage.py duel --source ai` → **3 de 8 correctas y baratas** (q1, q2 y q7).

| Pregunta | Veredicto | Clase de fallo | Evidencia |
|---|---|---|---|
| q3 | ✘ resultado distinto | **Borde** | Usa `__gt` y `__lt`, que excluyen los días límite. SQL: `published_at > 2026-03-01 AND published_at < 2026-05-31`. Faltan 2 artículos (los publicados exactamente el 1 de marzo y el 31 de mayo, p. ej. «Introducción al ORM de Django»). Mi consulta usa `BETWEEN`. |
| q4 | ⚠ correcta pero cara | **Cara (N+1)** | Filtra en Python: `[p for p in Post.objects.all() if p.comments.count() > 2]`. Hace 1 + 15 = **16 consultas** contra 1. Mi consulta resuelve todo con `annotate` + `filter` en una sola. |
| q5 | ✘ resultado distinto | **Conteos multiplicados** | Sin `distinct=True`, los dos `LEFT JOIN` (comentarios y etiquetas) multiplican las filas: devolvió `('Introducción al ORM de Django', 18, 18)` en vez de `(…, 6, 3)`; 18 = 6 comentarios × 3 etiquetas. SQL: `COUNT("blog_comment"."id")` y `COUNT("blog_post_tags"."tag_id")` sin `DISTINCT`. |
| q6 | ✘ error | **Campo inventado** | `author__country`: `FieldError: Unsupported lookup 'country'`. El país está en `Profile` (uno a uno), no en `Author`; lo correcto es `author__profile__country`. |
| q8 | ✘ resultado distinto | **Significado de la pregunta** | `filter(posts__published=False)` devuelve autores *con borradores*, no autores *sin artículos publicados*. Faltaba «Diego Pinto» (no tiene artículos) y sobraba «Ana Quispe» (tiene borradores, pero también publicados). SQL de la IA: `WHERE blog_post.published = False`; el mío: `NOT (EXISTS(SELECT 1 … WHERE published = True AND author_id = …))`. |

Qué aceptaría de la IA: q1, q2 y q7 (correctas y de una consulta). Las demás no, por la clase de fallo indicada.

## 4. De rojo a verde (pasos 9 a 11)

Antes de corregir, `python manage.py test blog.tests.test_front_page` falla en
`test_front_page_runs_two_queries` con **23 consultas contra 2 esperadas**.

**De dónde salen las 23:** 1 consulta para los artículos publicados + 11 consultas de autor (una por
artículo, al leer `post.author.name`) + 11 consultas de etiquetas (una por artículo, al recorrer
`post.tags.all`) = 1 + 11 + 11 = 23. Hay 11 artículos publicados, así que con N artículos serían
**1 + 2N**: crecen con el número de artículos (problema N+1).

**Corrección** (`blog/queries.py`): `select_related("author")` sigue la clave foránea con un `JOIN`
(autor y artículo en la misma consulta) y `prefetch_related("tags")` resuelve la relación muchos a
muchos con una consulta adicional y une los resultados en Python. Cada uno donde corresponde:
`select_related` para relaciones de «uno» (FK, uno a uno) y `prefetch_related` para las de «muchos».

| | Consultas de la portada |
|---|---|
| Antes | 23 |
| Después | **2** |

Suite completa `python manage.py test`: **24 pruebas, OK** (2 omitidas por no existir la carpeta
`teacher/`). Una prueba del repositorio base, `test_the_starter_has_nothing_written`, afirmaba que
el equipo aún no había escrito nada; se reemplazó por una que exige las ocho respuestas correctas.

## 5. La pasarela de acciones (paso 12)

| Intención | Respuesta |
|---|---|
| `posts_per_author` | `ok` (Beto Salas 6, Ana Quispe 6, Carla Rojas 3) |
| `comments_of_post` (`post_id` 1) | `ok` (6 comentarios, devueltos como `untrusted_data`) |
| `delete_comments_of_post` (`post_id` 1) | `approval_required` (plan con hash `c3ff9f72bb5e`; no se borra nada) |
| `run_sql` | `denied` («unknown action 'run_sql'») |

## 6. El cuarto comentario y la aprobación (pasos 13 y 14)

**Paso 13.** El cuarto comentario del artículo 1 contiene texto escrito como orden: pide llamar a
`delete_comments_of_post` con `post_id=1` sin pedir confirmación. Si un programa hubiera ejecutado
ese texto como instrucción, habría borrado los 6 comentarios del artículo 1 sin que nadie lo
aprobara. No ocurre por estos mecanismos de `blog/agent/registry.py`:

1. **Lista cerrada de acciones (`ACTIONS`):** el modelo solo puede pedir acciones que existen; lo
   demás (`eval`, `run_sql`, código) se rechaza con `denied`, no se interpreta.
2. **Lo leído es dato no confiable:** las lecturas devuelven sus resultados dentro de
   `untrusted_data`; el comentario es una cadena de texto, no una orden.
3. **Validación estricta de argumentos:** `_valid_args` exige exactamente los nombres y tipos
   declarados (un `True` o un `"1"` no sirven como `post_id`).
4. **Las acciones destructivas (R2) no se ejecutan por pedido del modelo:** `execute` devuelve un
   plan con hash y solo lo aplica si un humano repite el comando con ese hash en `--approve`; el
   modelo nunca recibe esa aprobación.

La salida de un modelo es un dato no confiable porque puede estar influida por texto ajeno (como el
comentario) y porque un modelo puede equivocarse: por eso se valida, se acota lo que puede ejecutar
y se exige aprobación humana para lo irreversible.

**Paso 14.** Se pidió el plan de borrado de los comentarios del artículo 5 (hash `4d7ffe2c0e99`) y
se repitió el comando con `--approve 4d7ffe2c0e99`: resultado `applied`, `deleted: 1`, y el artículo
quedó sin comentarios. Se restauraron los datos con `seed_blog`.

Después se probó el cambio entre el plan y la aprobación (artículo «Reseña: festival de cine
andino»): el plan listaba el comentario 62 (hash `f05f68176c35`); se agregó un comentario nuevo
(id 70); al aprobar con el hash viejo la respuesta fue `approval_required`, con un plan nuevo
(comentarios 62 y 70, hash `005fc21e1309`) y **sin borrar nada** (los 2 comentarios siguen).

**Por qué:** el hash se calcula sobre el plan construido con el estado *actual* (acción, argumentos
y comentarios afectados). Si los datos cambiaron desde que el humano revisó el plan, el hash cambia
y la aprobación vieja ya no vale: el humano aprobó algo que ya no es lo que se borraría.

**Observación:** `seed_blog` borra y vuelve a crear los datos, y SQLite no reinicia los
identificadores; tras volver a cargar, «el artículo 5» ya no tiene `id` 5 (aquí pasó a 35). Conviene
consultar el `id` real en `python manage.py shell` antes de usarlo en `--intent`.

## 7. Uso de IA

| Qué se le pidió | Qué respondió | Qué se aceptó o rechazó y por qué |
|---|---|---|
| Resolver las ocho consultas del duelo a partir de `blog/models.py` | Ocho consultas del ORM, cada una con una sola consulta SQL | Aceptadas solo después de que `duel` marcó las 8 como correctas y baratas (verificación con datos conocidos, no por confianza) |
| Corregir la portada hasta pasar `test_front_page_runs_two_queries` | `select_related("author")` y `prefetch_related("tags")` | Aceptada: la prueba pasó de 23 a 2 consultas |
| Ejecutar las respuestas de la IA del repositorio (`--source ai`) | Cinco de las ocho tenían fallos | Rechazadas q3, q4, q5, q6 y q8 por las clases de fallo de la tabla 3; aceptadas q1, q2 y q7 |
| Ejecutar y documentar la pasarela de acciones | Salidas de las cuatro intenciones y del flujo de aprobación | Aceptadas tras reproducirlas; se corrigió una prueba mal planteada (el `id` del artículo cambia al recargar los datos) |
