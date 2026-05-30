# Document Edit V1 Reference

- **Author:** OpenCode
- **Date:** 2026-05-29
- **Status:** Implemented (V1)
- **Scope:** Ref-stable page-element edits in the Parse workspace

---

## 1. What is implemented

The current document-edit feature supports optimistic page-element editing of existing Docling elements in the Parse workspace.

Implemented command set:

- `update_page_element`

Implemented session operations:

- load edit session
- queue page-element edit command
- commit pending commands
- discard pending commands

Implemented API routes:

- `GET /api/documents/{doc_id}/edits/session`
- `POST /api/documents/{doc_id}/edits/commands`
- `POST /api/documents/{doc_id}/edits/commit`
- `DELETE /api/documents/{doc_id}/edits/session`

## 2. Current command model

Backend action enum:

```python
class DocumentEditAction(StrEnum):
    UPDATE_PAGE_ELEMENT = "update_page_element"
```

Persisted command shape:

```json
{
  "id": "uuid",
  "analysisId": "analysis-uuid",
  "action": "update_page_element",
  "targetRef": "#/texts/12",
  "payload": {
    "content": "Updated content",
    "bbox": [10, 20, 110, 60],
    "type": "section_header"
  },
  "actor": "user",
  "at": "2026-05-29T12:34:56+00:00",
  "status": "pending"
}
```

Request shape sent to the unified command endpoint:

```json
{
  "commands": [
    {
      "action": "update_page_element",
      "targetRef": "#/texts/12",
      "payload": {
        "content": "Updated content",
        "bbox": [10, 20, 110, 60],
        "type": "section_header"
      }
    }
  ]
}
```

Semantics:

- `targetRef` points to an existing Docling item by `self_ref`
- `payload.content` replaces the item's current text when the item supports text
- `payload.bbox` updates the item's provenance bbox in frontend top-left coordinates
- `payload.type` updates the item's label only when the Docling item family safely supports that target type
- the command is append-only in `document_edits`
- pending commands are replayed from the latest committed `document_json`

## 3. What is not implemented yet

Not implemented in V1:

- `merge_texts`
- `reparent_item`
- insert/delete commands
- undo/redo
- optimistic tree regeneration during draft editing
- ref remapping after structural mutations

The main reason is `self_ref` stability. Structural Docling mutations can renumber refs, so V1 is intentionally limited to ref-stable field updates on existing elements.

## 4. Runtime flow

### 4.1 Load session

When the Parse workspace opens, the frontend loads the active analysis and then asks the backend for the current edit session. If pending commands exist, the backend replays them and returns the draft pages.

```mermaid
sequenceDiagram
    participant UI as Parse UI
    participant Store as documentStore
    participant API as document edit API
    participant Service as DocumentEditService
    participant Repo as analysis_repo + document_edit_repo

    UI->>Store: loadWorkspace(docId)
    Store->>Repo: fetch active analysis
    Store->>API: GET /api/documents/{docId}/edits/session
    API->>Service: get_session(docId)
    Service->>Repo: find latest completed analysis
    Service->>Repo: find pending document edits
    Service->>Service: load document_json
    Service->>Service: replay pending commands
    Service->>Service: regenerate pages
    Service-->>API: analysisId + pages + pendingCommands
    API-->>Store: session payload
    Store-->>UI: base pages or draft pages
```

### 4.2 Queue page-element edit

The user edits content, bbox, or type in `ElementProperties.vue`. The frontend updates the selected page element immediately, then persists an `update_page_element` command to the backend through the unified command endpoint.

```mermaid
sequenceDiagram
    participant User
    participant UI as ElementProperties
    participant Store as documentStore
    participant API as document edit API
    participant Service as DocumentEditService
    participant DB as document_edits

    User->>UI: Edit content / bbox / type
    UI->>Store: updatePageElement(docId, targetRef, payload)
    Store->>Store: optimistic page update by self_ref
    Store->>API: POST /api/documents/{docId}/edits/commands
    API->>Service: apply_commands(...)
    Service->>Service: load latest document_json
    Service->>Service: replay old pending commands
    Service->>Service: apply new update_page_element command
    Service->>Service: regenerate pages
    Service->>DB: insert pending command row
    Service-->>API: updated pages + pendingCommands
    API-->>Store: confirmed draft session
    Store-->>UI: synced draft pages
```

## 5. Commit flow

Commit uses the frontend draft pages as the optimistic expectation. The backend replays pending commands onto canonical `document_json`, regenerates pages, and compares the result before persisting.

```mermaid
sequenceDiagram
    participant UI as Parse UI
    participant Store as documentStore
    participant API as document edit API
    participant Service as DocumentEditService
    participant Repo as analysis_repo + document_edit_repo

    UI->>Store: commitPendingDocumentEdits(docId)
    Store->>API: POST /api/documents/{docId}/edits/commit(frontendPages)
    API->>Service: commit(docId, frontendPages)
    Service->>Repo: load latest completed analysis
    Service->>Repo: load pending document edits
    Service->>Service: replay commands on document_json
    Service->>Service: regenerate pages
    Service->>Service: compare frontendPages vs backendPages

    alt inconsistent
        Service-->>API: committed=false, consistent=false, differences, pages
        API-->>Store: commit failure payload
        Store-->>UI: replace draft pages with backend pages
    else consistent
        Service->>Repo: update analysis document_json/pages_json/content_markdown/content_html
        Service->>Repo: mark edits committed
        Service-->>API: committed=true, consistent=true, pages
        API-->>Store: commit success payload
        Store->>Repo: refetch active analysis
        Store-->>UI: draft cleared, committed pages active
    end
```

## 6. Flow diagrams

### 6.1 High-level architecture

```mermaid
flowchart LR
    A[User edits page element] --> B[ElementProperties.vue]
    B --> C[documentStore optimistic draft pages]
    C --> D[POST /edits/commands]
    D --> E[DocumentEditService]
    E --> F[Replay pending commands on document_json]
    F --> G[Regenerate pages from DoclingDocument]
    G --> H[Return canonical draft pages]
    H --> C
```

### 6.2 Commit decision flow

```mermaid
flowchart TD
    A[Commit pending edits] --> B[Load latest committed analysis]
    B --> C[Replay pending commands]
    C --> D[Regenerate backend pages]
    D --> E{Frontend pages match backend pages?}
    E -- No --> F[Return differences and backend pages]
    F --> G[Keep session uncommitted]
    E -- Yes --> H[Persist document_json]
    H --> I[Persist pages_json]
    I --> J[Persist markdown/html]
    J --> K[Mark commands committed]
    K --> L[Clear frontend draft]
```

## 7. Files involved

Backend:

- `document-parser/domain/value_objects.py`
- `document-parser/domain/models.py`
- `document-parser/domain/ports.py`
- `document-parser/persistence/database.py`
- `document-parser/persistence/document_edit_repo.py`
- `document-parser/services/document_edit_service.py`
- `document-parser/api/schemas.py`
- `document-parser/api/document_edits.py`
- `document-parser/main.py`

Frontend:

- `frontend/src/shared/types.ts`
- `frontend/src/features/document/api.ts`
- `frontend/src/features/document/store.ts`
- `frontend/src/pages/DocParseTab.vue`
- `frontend/src/features/document/ui/ElementProperties.vue`
- `frontend/src/shared/i18n.ts`

## 8. Important design constraints

- `document_json` is the source of truth
- `pages_json` is derived output
- optimistic frontend state is allowed to be temporary
- backend replay is canonical
- commit must compare regenerated backend pages with frontend draft pages before persisting
- V1 is intentionally limited to ref-stable field edits to avoid `self_ref` renumbering problems from structural Docling edits

## 9. Extension path

Likely next commands:

1. `merge_texts`
2. `reparent_item`
3. insert/delete with ref remapping
4. undo/redo on top of the command log
5. broader type-family conversions if class replacement becomes necessary
