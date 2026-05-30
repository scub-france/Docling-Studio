# Design: Document edit command workflow

- **Issue:** n/a
- **Title on issue:** Document edits with optimistic frontend projection and backend command application
- **Author:** OpenCode
- **Date:** 2026-05-29
- **Status:** Draft
- **Target milestone:** n/a
- **Impacted layers:** backend (`domain`, `persistence`, `services`, `api`) · frontend (`features/document`, `shared`) · docs
- **Audit dimensions likely touched:** DDD · Decoupling · KISS · Tests · Documentation
- **ADR spawned?:** no

---

## 1. Problem

The document workspace can render `pages_json`, tree nodes, and chunks derived from the latest completed analysis, but it cannot edit the underlying Docling document. Users need edits to appear immediately in the frontend while also being captured as commands that can be applied to the canonical `document_json` on the backend.

Once commands are applied, the backend must regenerate the derived projections from the mutated Docling document and compare the regenerated page details with the optimistic frontend state so inconsistencies are visible instead of silently accepted.

## 2. Goals

- [ ] Define a document edit session model that supports optimistic frontend edits and backend command persistence.
- [ ] Keep `document_json` as the editable source of truth; regenerate `pages_json` and tree from it after command application.
- [ ] Implement a safe V1 with ref-stable operations only: `update_page_element` first, then other non-structural edits.
- [ ] Add commit-time consistency verification between backend-regenerated page details and frontend optimistic page details.
- [ ] Preserve the existing workspace behavior for documents with no active edit session.

## 3. Non-goals

- Structural insert/delete commands in V1.
- Regenerating preview images as part of the optimistic edit loop.
- Reworking chunk editing, chunk diff, or push workflows.
- Multi-user collaborative editing or live session sharing.
- Full undo/redo in the first slice unless it falls out naturally from the command log.

## 4. Context & constraints

### 4.1 Current architecture

- `document_json` is already stored on completed analyses and is the only canonical representation that can drive both page details and tree projections.
- `pages_json` is derived by `document-parser/infra/local_converter.py:_extract_pages_detail`.
- Document tree nodes are derived from `document_json` via existing tree helpers in `document-parser/services/chunk_service.py` and `document-parser/infra/docling_tree.py`.
- Frontend parse rendering is currently analysis-driven via `frontend/src/features/document/store.ts` and has no local edit overlay state.

### 4.2 Hard constraints

- `self_ref` is the current cross-view identity key, but Docling can renumber refs on structural mutations.
- Frontend and backend command semantics must not diverge; optimistic projection should stay narrow and backend semantics stay canonical.
- New backend routes should stay document-scoped rather than analysis-scoped.
- Existing read paths must continue to work when no edit session exists.

### 4.3 V1 scope constraint

The first implementation slice should avoid operations that renumber `self_ref`. That keeps the optimistic and backend command targets stable while the workflow is introduced.

## 5. Proposed design

### 5.1 Domain

Add document-edit command types beside the existing chunk edit concepts.

Suggested V1 domain types:

```python
class DocumentEditAction(StrEnum):
    UPDATE_PAGE_ELEMENT = "update_page_element"


@dataclass(frozen=True)
class DocumentEditCommand:
    id: str
    document_id: str
    action: DocumentEditAction
    target_ref: str
    payload: dict
    actor: str
    at: datetime


@dataclass(frozen=True)
class DocumentEditDiff:
    ref: str
    field: str
    frontend: object | None
    backend: object | None
```

V1 keeps the command model intentionally small. `payload` can later branch by action without changing persistence layout.

### 5.2 Persistence

Add an append-only `document_edits` table modeled after `chunk_edits`.

```sql
CREATE TABLE IF NOT EXISTS document_edits (
    id            TEXT PRIMARY KEY,
    document_id   TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    analysis_id   TEXT NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    action        TEXT NOT NULL,
    target_ref    TEXT NOT NULL,
    payload_json  TEXT NOT NULL,
    actor         TEXT NOT NULL DEFAULT 'system',
    at            TEXT NOT NULL,
    session_id    TEXT,
    status        TEXT NOT NULL DEFAULT 'pending'
);
CREATE INDEX IF NOT EXISTS idx_document_edits_doc_at ON document_edits(document_id, at);
CREATE INDEX IF NOT EXISTS idx_document_edits_doc_session ON document_edits(document_id, session_id);
```

V1 can avoid a separate session table if the latest open session is addressed by `document_id` and `status='pending'` rows, but a dedicated session table is acceptable if state management becomes awkward.

### 5.3 Infra adapters

No new external infra is needed.

Refactor existing projection logic into reusable helpers so edit commits can regenerate the same projections as initial analysis finalization:

- page details from a `DoclingDocument`
- serialized `document_json`
- tree nodes from serialized `document_json`

### 5.4 Services

Add `document-parser/services/document_edit_service.py`.

Primary responsibilities:

1. Load the latest completed analysis for a document.
2. Parse `document_json` into a `DoclingDocument`.
3. Apply V1 commands to the document.
4. Regenerate derived projections.
5. Compare regenerated pages with the frontend optimistic pages.
6. Persist audit rows and, on commit, persist the updated analysis snapshot.

Suggested service surface:

```python
class DocumentEditService:
    async def get_session(self, document_id: str) -> DocumentEditSession: ...
    async def apply_commands(self, document_id: str, commands: list[dict], *, actor: str = "system") -> DocumentEditPreview: ...
    async def commit(self, document_id: str, frontend_pages: list[dict], *, actor: str = "system") -> DocumentEditCommitResult: ...
```

`apply_commands()` should apply the commands to a fresh document built from the latest committed snapshot plus all pending commands. That keeps backend preview behavior deterministic without needing mutable session state in memory.

`commit()` should:

1. reload the latest completed analysis
2. reapply pending commands
3. regenerate `pages_json`
4. compare backend pages vs frontend pages using semantic comparison with bbox tolerance
5. fail with structured diffs if inconsistent
6. write updated `document_json`, `pages_json`, and other derived fields back to the analysis snapshot
7. mark committed command rows as committed

### 5.5 API

Expose document-scoped routes.

```text
GET  /api/documents/{id}/edits/session
POST /api/documents/{id}/edits/commands
POST /api/documents/{id}/edits/commit
```

Suggested DTOs:

```python
class DocumentEditCommandRequest(BaseModel):
    action: str
    targetRef: str
    payload: dict = Field(default_factory=dict)


class ApplyDocumentEditCommandsRequest(BaseModel):
    commands: list[DocumentEditCommandRequest] = Field(default_factory=list)


class CommitDocumentEditsRequest(BaseModel):
    frontendPages: list[dict]


class DocumentEditPreviewResponse(BaseModel):
    pages: list[dict]
    pendingCommands: list[dict]


class DocumentEditCommitResponse(BaseModel):
    consistent: bool
    differences: list[dict]
    pages: list[dict]
```

V1 can keep DTOs generic around `pages` if the backend already serializes the page-detail dataclasses the same way as `pages_json`.

### 5.6 Frontend

Extend `frontend/src/features/document/store.ts` with draft edit state:

- `workspaceBasePages`
- `workspaceDraftPages`
- `pendingDocumentCommands`
- `hasDocumentEditSession`

Add actions:

- `startDocumentEditSession()`
- `updatePageElement(targetRef, payload)`
- `commitDocumentEdits()`
- `discardDocumentEdits()`

The optimistic path should stay narrow in V1:

1. update `workspaceDraftPages` by `self_ref`
2. queue an `update_page_element` command locally
3. persist the command through the unified document-edit command API
4. leave preview PNG rendering unchanged

UI changes:

- `DocParseTab.vue`: read effective pages from draft-or-base state
- `ElementProperties.vue`: add editable page-element form and save action for content, bbox, and type
- keep `PagePreviewWithOverlay.vue` unchanged except for consuming the effective pages already passed by the page

### 5.7 Consistency verification

Comparison must be semantic, not string-based.

Compare by `self_ref` and field values:

- `type`
- `content`
- `level`
- `bbox` with numeric tolerance

If comparison fails, return a structured diff payload and do not silently commit. The frontend should replace optimistic state with backend truth only after an explicit user action or a successful consistent commit.

## 6. Implementation plan

### Slice 1: Backend foundation

- Add `DocumentEditAction` and minimal command/response models.
- Add `document_edits` persistence and repository.
- Add `DocumentEditService` with `update_page_element` preview + commit skeleton.
- Extract or reuse projection helpers so edit commits regenerate page details the same way as analysis finalization.

### Slice 2: Frontend optimistic page-element editing

- Add document edit draft state to `features/document/store.ts`.
- Switch parse view to draft-or-base pages.
- Add content, bbox, and safe type editing controls in `ElementProperties.vue`.
- Persist `update_page_element` commands through the new API.

### Slice 3: Commit and verification

- Send optimistic pages with commit.
- Perform backend semantic diff.
- Return structured mismatches.
- Refresh workspace analysis/tree after successful commit.

### Slice 4: Extension path

- Add bbox edits.
- Add merge/reparent only if ref remapping is handled explicitly.
- Consider undo/redo once the command log and replay loop are stable.

## 7. Risks

- Structural Docling mutations can renumber `self_ref` and invalidate queued commands.
- Tree and chunk references may drift if future commands change document structure.
- If frontend local projection evolves beyond simple field replacement, it may diverge from backend semantics.

## 8. Testing strategy

- Backend unit tests for command replay, projection regeneration, and consistency diffing.
- API tests for page-element edit preview and commit success/failure cases.
- Frontend store tests for optimistic page updates.
- UI test for editing page element fields and observing immediate overlay/properties updates.

## 9. Decision

Proceed with a ref-stable V1 built around optimistic page projection, append-only document edit commands, backend regeneration from `document_json`, and commit-time consistency checks. The implemented command should start with `update_page_element` and support only safe field-level mutations.
