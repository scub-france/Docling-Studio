# Plan de remediation — Release 0.5.0

**Date** : 2026-04-22
**Branche** : `feature/reasoning-trace` -> `release/0.5.0`
**Entree** : [summary.md](summary.md) (audit complet)
**Objectif** : passer de NO-GO (2 CRIT, 5 MAJ) a GO.

---

## Sequencement global

```
Phase 1 (jour 1)        Phase 2 (jour 2-3)         Phase 3 (jour 4-5)         Phase 4 (jour 5)
-------------           -----------------           -----------------          ---------------
[M4 + B1]               [M1 + M2 + M3 + Q1]         [B2]                       [M5 + Q2-Q6]
Port Graph/Converter    Service refactor backend    Decouplage frontend        Cleanup + docs
~1 jour                 ~1.5 jour                   ~2 jours                   ~0.5 jour
```

**Dependances** :
- B1 et M4 touchent le meme port -> faire ensemble.
- M1/M2 beneficient de B1 (les services n'importent plus `infra.neo4j` avant qu'on casse leur code).
- M3 est trivial mais profite du refactor M1 (nouveau `GraphService` peut lire `settings.max_graph_pages`).
- Q1 tombe naturellement quand on migre la camelCase vers `api/schemas.py` dans le refactor M1.
- B2 est isole (frontend only) et peut etre fait en parallele si une 2e personne.
- M5 + Q5 + Q6 sont des edits ponctuels, dernier jour.

**Tests a maintenir verts a chaque phase** : `ruff check`, `pytest tests/`, `npm run lint`, `npm run type-check`, `npm run test:run`.

---

## Phase 1 — Ports (M4 + B1) ≈ 1 jour

### Step 1.1 : Elargir `DocumentConverter` port (resout M4)

**Fichier** : `document-parser/domain/ports.py`

```python
class DocumentConverter(Protocol):
    async def convert(
        self,
        file_path: str,
        options: ConversionOptions,
        *,
        page_range: tuple[int, int] | None = None,
    ) -> ConversionResult: ...

    # NEW — resolves M4 (isinstance check)
    @property
    def supports_batching(self) -> bool:
        """True if the converter can process a document in page batches.

        Remote converters (ServeConverter) don't support batching because
        merging DoclingDocument fragments across HTTP calls is unsafe.
        """
        ...
```

**Fichier** : `document-parser/infra/local_converter.py`

```python
class LocalConverter:
    supports_batching: bool = True
    # ... reste inchange
```

**Fichier** : `document-parser/infra/serve_converter.py`

```python
class ServeConverter:
    supports_batching: bool = False
    # ... reste inchange
```

**Fichier** : `document-parser/services/analysis_service.py`

```python
# Supprimer la methode _is_remote_converter et son import ServeConverter
# Remplacer l'appel :
#   is_remote = self._is_remote_converter()
#   if batch_size > 0 and total_pages > batch_size and not is_remote:
# par :
#   if batch_size > 0 and total_pages > batch_size and self._converter.supports_batching:
```

**Tests impactes** : `tests/test_serve_converter.py`, `tests/test_analysis_service.py` (mocker `supports_batching` sur le mock converter).

---

### Step 1.2 : Creer `GraphWriter` port (resout B1)

**Fichier** : `document-parser/domain/ports.py` (ajout)

```python
@runtime_checkable
class GraphWriter(Protocol):
    """Port for persisting the DoclingDocument structure + chunks to a graph store.

    Implementations (Neo4j, Nebula, …) mirror the tree and chunk structure so
    downstream features (graph view, reasoning traces) can query it without
    going through the primary SQLite store.
    """

    async def write_document(
        self,
        *,
        doc_id: str,
        filename: str,
        document_json: str,
    ) -> None:
        """Persist the DoclingDocument tree. Idempotent (replaces existing)."""
        ...

    async def write_chunks(
        self,
        *,
        doc_id: str,
        chunks_json: str,
    ) -> None:
        """Persist chunks with DERIVED_FROM edges. Idempotent."""
        ...
```

### Step 1.3 : Creer l'adapter `Neo4jGraphWriter`

**Nouveau fichier** : `document-parser/infra/neo4j/graph_writer.py`

```python
"""Neo4jGraphWriter — GraphWriter port implementation over Neo4j.

Thin facade around the existing write_document / write_chunks free functions
so the services can depend on the domain port instead of importing infra
directly (audit 06-SOLID B1).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from infra.neo4j.chunk_writer import write_chunks as _write_chunks
from infra.neo4j.tree_writer import write_document as _write_document

if TYPE_CHECKING:
    from infra.neo4j.driver import Neo4jDriver


class Neo4jGraphWriter:
    """Implements domain.ports.GraphWriter over a Neo4j driver."""

    def __init__(self, driver: Neo4jDriver) -> None:
        self._driver = driver

    async def write_document(
        self,
        *,
        doc_id: str,
        filename: str,
        document_json: str,
    ) -> None:
        await _write_document(
            self._driver,
            doc_id=doc_id,
            filename=filename,
            document_json=document_json,
        )

    async def write_chunks(self, *, doc_id: str, chunks_json: str) -> None:
        await _write_chunks(self._driver, doc_id=doc_id, chunks_json=chunks_json)
```

### Step 1.4 : Cabler dans `main.py` + services

**Fichier** : `document-parser/main.py`

```python
# Remplacer les signatures et le wiring :
def _build_analysis_service(
    document_repo, analysis_repo, graph_writer: GraphWriter | None = None,
) -> AnalysisService:
    ...
    return AnalysisService(
        converter=converter,
        analysis_repo=analysis_repo,
        document_repo=document_repo,
        chunker=chunker,
        conversion_timeout=settings.conversion_timeout,
        max_concurrent=settings.max_concurrent_analyses,
        config=config,
        graph_writer=graph_writer,  # remplace neo4j_driver=
    )


async def lifespan(app: FastAPI):
    await init_db()
    document_repo, analysis_repo = _build_repos()
    app.state.analysis_repo = analysis_repo
    app.state.document_repo = document_repo
    app.state.neo4j = await _init_neo4j()

    # NEW — build graph writer once, inject via port
    graph_writer = None
    if app.state.neo4j is not None:
        from infra.neo4j.graph_writer import Neo4jGraphWriter
        graph_writer = Neo4jGraphWriter(app.state.neo4j)
    app.state.graph_writer = graph_writer

    app.state.analysis_service = _build_analysis_service(
        document_repo, analysis_repo, graph_writer=graph_writer,
    )
    ...
    ingestion_service = _build_ingestion_service(graph_writer=graph_writer)
```

**Fichier** : `document-parser/services/analysis_service.py`

```python
# Remplacer :
#   neo4j_driver=None
#   from infra.neo4j import write_document
#   await write_document(self._neo4j, ...)
# par :
#   graph_writer: GraphWriter | None = None
#   await self._graph_writer.write_document(doc_id=..., filename=..., document_json=...)
```

**Fichier** : `document-parser/services/ingestion_service.py`

```python
# Remplacer :
#   neo4j_driver=None
#   from infra.neo4j import write_chunks
#   await write_chunks(self._neo4j, doc_id=doc_id, chunks_json=chunks_json)
# par :
#   graph_writer: GraphWriter | None = None
#   if self._graph_writer is not None:
#       await self._graph_writer.write_chunks(doc_id=doc_id, chunks_json=chunks_json)
```

**Tests impactes** :
- `tests/test_analysis_service.py` : mocker `GraphWriter` au lieu du driver neo4j.
- `tests/test_ingestion_service.py` : idem.
- `tests/neo4j/test_document_roundtrip.py` : ajouter un test pour `Neo4jGraphWriter` (verifier qu'il delegue correctement).

**Risques** :
- La branche existante exposait `app.state.neo4j` (driver brut) sur d'autres consommateurs ? -> grep dans `api/*.py` montre seulement `api/graph.py` qui utilise le driver pour READ (fetch_graph). OK, pas de casse cote read.

**Check de validation** :
```bash
grep -rn "from infra.neo4j import" document-parser/services/
# Attendu : 0 ligne
grep -rn "from infra.serve_converter import" document-parser/services/
# Attendu : 0 ligne
grep -rn "isinstance" document-parser/services/
# Attendu : 0 ligne
```

---

## Phase 2 — Services (M1 + M2 + M3 + Q1) ≈ 1.5 jour

### Step 2.1 : Creer `GraphService` (resout M1 partie graph + M3)

**Fichier** : `document-parser/infra/settings.py`

```python
# Ajouter :
max_graph_pages: int = 200  # cap pour /graph et /reasoning-graph (413 au-dela)

# Et dans from_env() :
max_graph_pages=int(os.environ.get("MAX_GRAPH_PAGES", "200")),
```

**Nouveau fichier** : `document-parser/services/graph_service.py`

```python
"""Graph service — orchestrates graph retrieval from Neo4j or SQLite fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from infra.docling_graph import build_graph_payload
from infra.neo4j.queries import GraphPayload, fetch_graph

if TYPE_CHECKING:
    from domain.ports import AnalysisRepository
    from infra.neo4j.driver import Neo4jDriver

logger = logging.getLogger(__name__)


@dataclass
class GraphTooLargeError(Exception):
    page_count: int
    max_pages: int


@dataclass
class GraphNotFoundError(Exception):
    doc_id: str


class GraphService:
    def __init__(
        self,
        *,
        analysis_repo: AnalysisRepository,
        neo4j_driver: Neo4jDriver | None = None,
        max_pages: int = 200,
    ) -> None:
        self._analysis_repo = analysis_repo
        self._neo4j = neo4j_driver
        self._max_pages = max_pages

    async def get_neo4j_graph(self, doc_id: str) -> GraphPayload:
        if self._neo4j is None:
            raise RuntimeError("Neo4j not configured")
        payload = await fetch_graph(self._neo4j, doc_id, max_pages=self._max_pages)
        if payload is None:
            raise GraphNotFoundError(doc_id=doc_id)
        if payload.truncated:
            raise GraphTooLargeError(page_count=payload.page_count, max_pages=self._max_pages)
        return payload

    async def get_reasoning_graph(self, doc_id: str) -> GraphPayload:
        latest = await self._analysis_repo.find_latest_completed_by_document(doc_id)
        if latest is None or not latest.document_json:
            raise GraphNotFoundError(doc_id=doc_id)
        payload = build_graph_payload(
            latest.document_json,
            doc_id=doc_id,
            title=latest.document_filename or doc_id,
            max_pages=self._max_pages,
        )
        if payload.truncated:
            raise GraphTooLargeError(page_count=payload.page_count, max_pages=self._max_pages)
        return payload
```

**Fichier** : `document-parser/api/graph.py` (simplifier)

```python
# Devient :
@router.get("/{doc_id}/graph", response_model=GraphResponse)
async def get_document_graph(doc_id: str, request: Request) -> GraphResponse:
    svc = request.app.state.graph_service
    try:
        payload = await svc.get_neo4j_graph(doc_id)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Neo4j is not configured")
    except GraphNotFoundError:
        raise HTTPException(status_code=404, detail=f"No graph for document {doc_id}")
    except GraphTooLargeError as e:
        raise HTTPException(status_code=413, detail=f"Graph too large: {e.page_count} pages (cap {e.max_pages})")
    return _payload_to_response(payload)

@router.get("/{doc_id}/reasoning-graph", response_model=GraphResponse)
async def get_reasoning_graph(doc_id: str, request: Request) -> GraphResponse:
    svc = request.app.state.graph_service
    try:
        payload = await svc.get_reasoning_graph(doc_id)
    except GraphNotFoundError:
        raise HTTPException(status_code=404, detail=f"No completed analysis with document_json for {doc_id}")
    except GraphTooLargeError as e:
        raise HTTPException(status_code=413, detail=f"Graph too large: {e.page_count} pages (cap {e.max_pages})")
    return _payload_to_response(payload)
```

**Fichier** : `document-parser/main.py` (ajouter le wiring)

```python
from services.graph_service import GraphService
app.state.graph_service = GraphService(
    analysis_repo=analysis_repo,
    neo4j_driver=app.state.neo4j,
    max_pages=settings.max_graph_pages,
)
```

### Step 2.2 : Creer `ReasoningService` (resout M1 partie reasoning + M2)

**Nouveau fichier** : `document-parser/services/reasoning_service.py`

```python
"""Reasoning service — orchestrates docling-agent's RAG loop against a stored doc."""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.ports import AnalysisRepository

logger = logging.getLogger(__name__)


@dataclass
class ReasoningConfig:
    enabled: bool = False
    ollama_host: str = "http://localhost:11434"
    default_model_id: str = "gpt-oss:20b"


class ReasoningDisabledError(Exception):
    pass


class ReasoningDepsNotInstalledError(Exception):
    pass


class DocumentNotReadyError(Exception):
    def __init__(self, doc_id: str):
        self.doc_id = doc_id


class LlmParseError(Exception):
    """Raised when the model cannot produce a parseable answer after retries."""
    def __init__(self, model_id: str):
        self.model_id = model_id


@dataclass
class RagIteration:
    iteration: int
    section_ref: str
    reason: str
    section_text_length: int
    can_answer: bool
    response: str


@dataclass
class RagResult:
    answer: str
    iterations: list[RagIteration]
    converged: bool


class ReasoningService:
    def __init__(
        self,
        *,
        analysis_repo: AnalysisRepository,
        config: ReasoningConfig,
    ) -> None:
        self._analysis_repo = analysis_repo
        self._config = config

    async def run(self, doc_id: str, query: str, model_id: str | None = None) -> RagResult:
        if not self._config.enabled:
            raise ReasoningDisabledError()

        latest = await self._analysis_repo.find_latest_completed_by_document(doc_id)
        if latest is None or not latest.document_json:
            raise DocumentNotReadyError(doc_id)

        try:
            from docling_agent.agents import DoclingRAGAgent
            from docling_core.types.doc.document import DoclingDocument
            from mellea.backends.model_ids import ModelIdentifier
        except ImportError as e:
            raise ReasoningDepsNotInstalledError() from e

        # See rapport-08 security INFO : to replace by kwarg once lib supports it
        os.environ["OLLAMA_HOST"] = self._config.ollama_host
        raw_model_id = model_id or self._config.default_model_id

        doc = DoclingDocument.model_validate_json(latest.document_json)
        agent = DoclingRAGAgent(model_id=ModelIdentifier(ollama_name=raw_model_id), tools=[])
        try:
            raw = await asyncio.to_thread(agent._rag_loop, query=query, doc=doc)
        except IndexError as e:
            raise LlmParseError(raw_model_id) from e

        return RagResult(
            answer=raw.answer,
            iterations=[RagIteration(**it.model_dump()) for it in raw.iterations],
            converged=raw.converged,
        )
```

**Fichier** : `document-parser/api/reasoning.py` (devient mince — ~50 lignes au lieu de 148)

```python
@router.post("/{doc_id}/rag", response_model=RagResultResponse)
async def run_rag(doc_id: str, body: RagRunRequest, request: Request) -> RagResultResponse:
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty")

    svc: ReasoningService = request.app.state.reasoning_service
    try:
        result = await svc.run(doc_id, body.query, body.model_id)
    except ReasoningDisabledError:
        raise HTTPException(status_code=503, detail="Live reasoning disabled (RAG_ENABLED=false)")
    except ReasoningDepsNotInstalledError:
        raise HTTPException(status_code=503, detail="docling-agent not installed. `pip install docling-agent mellea`.")
    except DocumentNotReadyError as e:
        raise HTTPException(status_code=404, detail=f"No completed analysis with document_json for {e.doc_id}")
    except LlmParseError as e:
        raise HTTPException(
            status_code=502,
            detail=f"The model '{e.model_id}' couldn't produce a parseable answer. Try a different model.",
        )
    return _result_to_response(result)
```

**Fichier** : `document-parser/main.py` (wiring)

```python
from services.reasoning_service import ReasoningConfig, ReasoningService

reasoning_config = ReasoningConfig(
    enabled=settings.rag_enabled,
    ollama_host=settings.ollama_host,
    default_model_id=settings.rag_model_id,
)
app.state.reasoning_service = ReasoningService(
    analysis_repo=analysis_repo,
    config=reasoning_config,
)
```

### Step 2.3 : Q1 — deplacer `_chunk_to_dict` vers `api/schemas.py`

**Fichier** : `document-parser/api/schemas.py`

```python
class ChunkBboxResponse(_CamelModel):
    page: int
    bbox: list[float]

class ChunkDocItemResponse(_CamelModel):
    self_ref: str
    label: str

class ChunkResponse(_CamelModel):
    text: str
    headings: list[str] = []
    source_page: int | None = None
    token_count: int = 0
    bboxes: list[ChunkBboxResponse] = []
    doc_items: list[ChunkDocItemResponse] = []
    modified: bool = False
    deleted: bool = False

def chunk_result_to_response(c: ChunkResult) -> ChunkResponse:
    return ChunkResponse(
        text=c.text,
        headings=c.headings,
        source_page=c.source_page,
        token_count=c.token_count,
        bboxes=[ChunkBboxResponse(page=b.page, bbox=b.bbox) for b in c.bboxes],
        doc_items=[ChunkDocItemResponse(self_ref=d.self_ref, label=d.label) for d in c.doc_items],
    )
```

**Fichier** : `document-parser/services/analysis_service.py`

```python
# Supprimer la fonction _chunk_to_dict (lignes 39-47)
# Le service retournera une liste de ChunkResult (domain), pas de dict.
# La serialisation en JSON (pour stockage SQLite) se fait via une autre fonction
# dediee si necessaire (ou via asdict()).
```

### Step 2.4 : M3 — purger `MAX_PAGES = 200` en dur

**Fichier** : `document-parser/api/graph.py`
- Supprimer `MAX_PAGES = 200` (ligne 24). Le cap vient maintenant de `GraphService._max_pages`.

**Fichier** : `document-parser/infra/docling_graph.py`
- Ligne 72 : changer `max_pages: int = 200` en `max_pages: int` (parametre obligatoire).

**Fichier** : `document-parser/infra/neo4j/queries.py`
- Ligne 147 : meme changement.

Verification :
```bash
grep -rn "max_pages.*=.*200\|MAX_PAGES" document-parser --include="*.py" --exclude-dir=.venv --exclude-dir=tests
# Attendu : seulement les tests (qui passent leur propre valeur)
```

**Tests impactes** :
- `tests/test_docling_graph.py` : verifier que les appels passent bien `max_pages`.
- `tests/test_graph_api.py` : idem.
- Nouveaux tests : `tests/test_graph_service.py`, `tests/test_reasoning_service.py` (extraire la logique testee dans test_graph_api.py et test_reasoning_api.py qui deviennent des tests HTTP fins).

---

## Phase 3 — Decouplage frontend (B2) ≈ 2 jours

### Strategie

Deux options :

**Option A — strict** : deplacer tous les composants partages vers `frontend/src/shared/ui/viewer/`.
- Plus long, meilleur score audit, mais refactor important des chemins d'import.

**Option B — pragmatique** : accepter `features/X/index.ts` comme "public API" d'une feature. Refuser uniquement les imports profonds (`features/X/ui/Y.vue`, `features/X/store`) depuis une autre feature.
- Plus rapide, necessite d'ajouter une lint rule pour enforcer.

**Recommande : mix A+B** :
- Composants reellement partages par 3+ features -> `shared/ui/`.
- Stores cross-feature -> remplacer par props au niveau page.
- Import via `features/X/index.ts` accepte si strictement public API (pas de store).

### Step 3.1 : Extraire styles reasoning du GraphView (casse le cycle)

**Fichier** : `frontend/src/features/analysis/ui/GraphView.vue`

```typescript
// Supprimer :
//   import { reasoningOverlayStyles } from '../../reasoning/graphReasoningOverlay'
// Ajouter dans defineProps :
const props = defineProps<{
  // ... existants
  extraStyles?: CytoscapeStyle[]  // Injected by parent feature (e.g. reasoning overlay)
}>()
// Dans la construction Cytoscape :
const allStyles = [...baseStyles, ...(props.extraStyles ?? [])]
```

**Fichier** : `frontend/src/features/reasoning/ui/ReasoningWorkspace.vue`

```typescript
// Importer le style localement :
import { reasoningOverlayStyles } from '../graphReasoningOverlay'
// Passer au GraphView via prop :
<GraphView ref="graphViewRef" :extra-styles="reasoningOverlayStyles" ... />
```

**Resultat** : le cycle `analysis <-> reasoning` est brise (reasoning depend d'analysis, pas l'inverse).

### Step 3.2 : Deplacer les composants reellement partages vers `shared/ui/viewer/`

Candidats (utilises par >= 2 features) :
- `StructureViewer.vue` — utilise par `analysis` ET `reasoning`
- `GraphView.vue` — utilise par `analysis` ET `reasoning`
- `BboxOverlay.vue` — utilise par `analysis` (+ futur reasoning)

Pas deplaces (utilises par 1 seul feature) :
- `NodeDetailsPanel.vue`, `ResultTabs.vue`, `MarkdownViewer.vue`, `ImageGallery.vue` — specifique `analysis`
- `AnalysisPanel.vue` — orchestrateur analysis, OK dans `features/analysis`

**Migration** :
```bash
mkdir -p frontend/src/shared/ui/viewer
git mv frontend/src/features/analysis/ui/StructureViewer.vue frontend/src/shared/ui/viewer/StructureViewer.vue
git mv frontend/src/features/analysis/ui/GraphView.vue frontend/src/shared/ui/viewer/GraphView.vue
git mv frontend/src/features/analysis/ui/BboxOverlay.vue frontend/src/shared/ui/viewer/BboxOverlay.vue
```

Mettre a jour les imports (14 fichiers environ). Utiliser l'alias `@/shared/ui/viewer/...`.

**Fichier** : `frontend/src/features/analysis/index.ts` — supprimer les re-exports de StructureViewer/BboxOverlay.

### Step 3.3 : `getPreviewUrl` vers `shared/api/documents.ts`

**Nouveau fichier** : `frontend/src/shared/api/documents.ts`

```typescript
/** Preview URL for a document page (served by the backend). */
export function getPreviewUrl(id: string, page = 1, dpi = 150): string {
  return `/api/documents/${id}/preview?page=${page}&dpi=${dpi}`
}
```

**Fichier** : `frontend/src/features/document/api.ts` — re-export pour compat interne mais consommer la version shared :
```typescript
export { getPreviewUrl } from '../../shared/api/documents'
```

**Fichier** : `frontend/src/features/analysis/ui/StructureViewer.vue` (devenu `shared/ui/viewer/`) et autres usages :
```typescript
import { getPreviewUrl } from '@/shared/api/documents'
```

### Step 3.4 : Eliminer les `useXxxStore` cross-feature

Schema cible : les stores d'un feature ne sont accedes qu'a l'interieur de ce feature. Cross-feature -> props au niveau page.

**Cas `chunking/ui/ChunkPanel.vue:228` -> `useAnalysisStore`** :
- Ce dont a besoin ChunkPanel : l'analyse en cours (pour connaitre les chunks).
- Fix : `StudioPage.vue` passe `:analysis="currentAnalysis"` a `<ChunkPanel>`.
- `ChunkPanel` devient purement driven par props.

**Cas `reasoning/ui/DocumentView.vue:34` -> `useAnalysisStore`** :
- Besoin : les pages du document analyse.
- Fix : passer `:pages="pages"` en prop (calcul au niveau `ReasoningWorkspace` ou `ReasoningPage`).

**Cas `reasoning/ui/ReasoningDocPicker.vue:82-83` -> `useAnalysisStore`, `useDocumentStore`** :
- Besoin : liste des documents + leur statut d'analyse.
- Fix : creer un `useReasoningEligibleDocs()` composable dans `reasoning/` qui FETCH directement via API (pas de dependance au store d'un autre feature). Ou : passer la liste filtree en prop depuis la page.

**Cas `analysis/ui/AnalysisPanel.vue:61` -> `useDocumentStore`** :
- Besoin : le document courant et sa liste.
- Fix : `AnalysisPanel` recoit `:documents`, `:selectedDocument` en props ; emits `@select-document`, `@upload-document`.

**Cas `settings/ui/SettingsPanel.vue:70` -> `useFeatureFlagStore`** :
- Feature-flags est transversal. Acceptable qu'un autre feature le lise.
- Mais strict audit : exposer via `useFeatureFlag()` composable dans `shared/composables/` plutot que le store directement.

**Fichier** : `frontend/src/shared/composables/useFeatureFlag.ts` (existe-t-il ? `grep` : oui, `frontend/src/features/feature-flags/useFeatureFlag.test.ts`). Deplacer le composable vers `shared/composables/` et laisser le store dans `features/feature-flags/`.

### Step 3.5 : Lint rule (ESLint) pour prevenir regression

**Fichier** : `frontend/eslint.config.js` (ou `.eslintrc`)

```javascript
{
  files: ['src/features/**/*.{ts,vue}'],
  rules: {
    'no-restricted-imports': ['error', {
      patterns: [
        {
          group: ['../../*/store', '../../*/ui/*', '../../*/api'],
          message: 'Features must not import from other features. Use shared/ or props/events.',
        },
      ],
    }],
  },
}
```

**Tests impactes** :
- Tout test important `features/analysis/ui/StructureViewer.vue` a renommer en `shared/ui/viewer/StructureViewer.vue`.
- `frontend/src/features/analysis/ui/StructureViewer.vue` existe-t-il comme fichier test ? Non, pas de `.test` pour les composants UI lourds (pattern du projet).

**Risques** :
- Casse des tests e2e Karate si les selecteurs `data-e2e` etaient dans les composants deplaces -> verifier (les selecteurs restent identiques si le composant n'est pas modifie, juste deplace).
- HMR peut etre capricieux pendant la migration -> faire un vrai restart du dev server.

---

## Phase 4 — Cleanup (M5 + Q2-Q6) ≈ 0.5 jour

### Step 4.1 : M5 — CHANGELOG `[Unreleased]`

**Fichier** : `CHANGELOG.md`

Ajouter entre la ligne 6 et 7 (`## [0.4.0]`) :

```markdown
## [Unreleased]

### Added

- Reasoning-trace viewer: import a `docling-agent` sidecar JSON and overlay RAG iterations on the document graph/PDF views
- Live reasoning runner: `POST /api/documents/:id/rag` invokes `docling-agent`'s Chunkless RAG loop against a stored DoclingDocument (disabled by default via `RAG_ENABLED=false`; requires Ollama reachable + `docling-agent` and `mellea` installed)
- Neo4j graph storage: DoclingDocument tree persisted via TreeWriter with Document/Element/Page/Provenance nodes; chunks persisted via ChunkWriter with DERIVED_FROM edges
- Graph API endpoints: `GET /api/documents/:id/graph` (Neo4j-backed, full graph with chunks) and `GET /api/documents/:id/reasoning-graph` (SQLite-only, no Neo4j dep)
- Frontend feature `reasoning/` with focus mode, iteration navigation, bidirectional graph/document sync
- Env vars: `RAG_ENABLED`, `OLLAMA_HOST`, `RAG_MODEL_ID`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `MAX_GRAPH_PAGES`
- Domain ports: `GraphWriter` (Neo4j-backed), `EmbeddingService`, `VectorStore`

### Changed

- Services no longer import `infra.neo4j` or `infra.serve_converter` directly — graph persistence goes through `GraphWriter` port; batching capability is exposed as `DocumentConverter.supports_batching` property (audit remediation 06-SOLID)
- `StructureViewer`, `GraphView`, `BboxOverlay` moved to `frontend/src/shared/ui/viewer/` (audit remediation 07-decoupling)

### Fixed

- (a completer)
```

### Step 4.2 : Q5 — `.env.example` complet

**Fichier** : `.env.example` (ajout en fin)

```bash
# --- Live reasoning (docling-agent runner) — disabled by default ---
# RAG_ENABLED=false
# OLLAMA_HOST=http://localhost:11434
# RAG_MODEL_ID=gpt-oss:20b

# --- Rate limiting (requests per minute per IP, 0 = disabled) ---
# RATE_LIMIT_RPM=100

# --- Timeouts (seconds) — must satisfy document < lock < conversion ---
# DOCUMENT_TIMEOUT=120
# LOCK_TIMEOUT=300
# CONVERSION_TIMEOUT=900

# --- Batch processing for very large PDFs (0 = disabled) ---
# BATCH_PAGE_SIZE=0

# --- OpenSearch max chunks returned per document ---
# OPENSEARCH_DEFAULT_LIMIT=1000

# --- Max pages per graph query (returns 413 beyond) ---
# MAX_GRAPH_PAGES=200

# --- Default table analysis mode: "accurate" or "fast" ---
# DEFAULT_TABLE_MODE=accurate
```

### Step 4.3 : Q6 — Nginx cache statique

**Fichier** : `nginx.conf` (inserer avant `location / {`)

```nginx
# Hashed assets (Vite emits content-hashed filenames) — cache 1 year
location ~* \.(?:js|css|woff2?|ttf|otf|svg|png|jpg|jpeg|webp|gif|ico)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    try_files $uri =404;
}
```

### Step 4.4 : Q2 — decouper les fonctions longues (non bloquant, best effort)

**Cibles prioritaires** (ordre de gain pedagogique) :
1. `infra/neo4j/tree_writer.py:67` `write_document` (228L) — decouper en :
   - `_wipe_existing(tx, doc_id)`
   - `_write_document_node(tx, doc_id, filename, ...)`
   - `_write_pages(tx, doc_id, pages)`
   - `_write_elements_and_provenances(tx, ...)`
   - `_write_structural_edges(tx, ...)`
2. `infra/neo4j/queries.py:143` `fetch_graph` (126L) — une helper par groupe de nodes/edges.
3. Si le refactor Phase 2 a bien fait son job, `api/reasoning.py:run_rag` et `api/graph.py:get_reasoning_graph` sont deja < 30L.

### Step 4.5 : Q3 — signatures avec dataclass context

**Fichier** : `document-parser/services/analysis_service.py`

```python
@dataclass
class AnalysisContext:
    job_id: str
    file_path: str
    filename: str
    pipeline_options: dict | None = None
    chunking_options: dict | None = None

# Remplacer :
#   async def _run_analysis(self, job_id, file_path, filename, pipeline_options, chunking_options)
# par :
#   async def _run_analysis(self, ctx: AnalysisContext)
```

**Fichier** : `document-parser/domain/models.py`

```python
@dataclass
class CompletionPayload:
    markdown: str
    html: str
    pages_json: str
    document_json: str | None = None
    chunks_json: str | None = None

# Sur AnalysisJob :
def mark_completed(self, payload: CompletionPayload) -> None:
    ...
```

### Step 4.6 : Q4 — splitter les gros composants Vue (planification)

Hors scope immediate — trop gros pour la fenetre 0.5.0. **Acter en dette** :
- `StudioPage.vue` (1450L) : a decouper en `StudioUploadSection.vue`, `StudioAnalysisSection.vue`, `StudioResultsSection.vue` en 0.6.
- `ChunkPanel.vue` (801L), `GraphView.vue` (695L), `ResultTabs.vue` (690L) : ticket dedie post-0.5.

---

## Re-audit delta apres remediations

Apres P1 + P2 + P3 + P4, **re-lancer uniquement** :

| Audit | Raison |
|-------|--------|
| 01 Hexa Arch | Verifier que M1 (graph+reasoning services) a elimine le MAJ |
| 03 Clean Code | Verifier run_rag < 30L et SRP ok |
| 05 DRY | Verifier MAX_PAGES purge |
| 06 SOLID | Verifier CRIT B1 resolu + MAJ M4 resolu |
| 07 Decouplage | Verifier CRIT B2 resolu (grep imports cross-feature hors `shared/`) |
| 10 CI/Build | Verifier `.env.example` complet |
| 11 Documentation | Verifier CHANGELOG + version bump |

Audits **02, 04, 08, 09, 12** : pas de changement attendu, on peut les skipper au re-audit.

Commande :
```
Re-audite uniquement les audits 01, 03, 05, 06, 07, 10, 11 sur la branche courante en suivant docs/audit/master.md
```

---

## Ordonnancement git/PR recommande

| PR | Branche | Contenu | Audits concernes |
|----|---------|---------|------------------|
| PR-A | `fix/0.5.0-port-graphwriter` | Phase 1 (B1 + M4) | 06 |
| PR-B | `fix/0.5.0-extract-services` | Phase 2 (M1 + M2 + M3 + Q1) | 01, 03, 05 |
| PR-C | `fix/0.5.0-frontend-decoupling` | Phase 3 (B2) | 07 |
| PR-D | `chore/0.5.0-release-prep` | Phase 4 (M5 + Q5 + Q6 + Q2 + Q3) | 10, 11 |

Chaque PR doit rester petit (revue + CI courte). Base : toutes branchees sur `release/0.5.0` cree depuis `feature/reasoning-trace` (en suivant la convention git flow du projet).

---

## Estimation globale

| Phase | Duree | Effort (dev-jour) |
|-------|-------|-------------------|
| 1 — Ports | 1j | 1 |
| 2 — Services | 1.5j | 1.5 |
| 3 — Frontend | 2j | 2 |
| 4 — Cleanup | 0.5j | 0.5 |
| **Total** | **5j** | **5 dev-jour** |

Avec 2 devs en parallele (un backend PR-A+B, un frontend PR-C+D), **3 jours calendaires** suffisent.

---

## Validation finale avant tag 0.5.0

- [ ] PR-A, B, C, D mergees dans `release/0.5.0`
- [ ] `ruff check . && ruff format --check .` vert
- [ ] `pytest tests/ -v` vert (backend)
- [ ] `npm run lint && npm run type-check && npm run test:run` vert (frontend)
- [ ] `npm run build` produit un bundle sans warning
- [ ] CI GitHub Actions verte sur `release/0.5.0`
- [ ] Re-audit delta ci-dessus repasse GO (CRIT = 0, MAJ <= 3)
- [ ] `CHANGELOG.md` : renommer `[Unreleased]` en `[0.5.0] - 2026-04-XX`
- [ ] `frontend/package.json` : bump `"version": "0.5.0"`
- [ ] Tag git `v0.5.0` sur `release/0.5.0`
