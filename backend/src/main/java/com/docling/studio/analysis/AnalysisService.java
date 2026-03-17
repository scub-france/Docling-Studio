package com.docling.studio.analysis;

import com.docling.studio.document.Document;
import com.docling.studio.document.DocumentParserClient;
import com.docling.studio.document.DocumentService;
import com.docling.studio.shared.exception.ResourceNotFoundException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
public class AnalysisService {

    private final AnalysisJobRepository repository;
    private final DocumentService documentService;
    private final DocumentParserClient parserClient;
    private final ObjectMapper objectMapper;

    public AnalysisService(
            AnalysisJobRepository repository,
            DocumentService documentService,
            DocumentParserClient parserClient,
            ObjectMapper objectMapper
    ) {
        this.repository = repository;
        this.documentService = documentService;
        this.parserClient = parserClient;
        this.objectMapper = objectMapper;
    }

    public AnalysisJob create(UUID documentId) {
        Document doc = documentService.findById(documentId);
        AnalysisJob job = new AnalysisJob(doc);
        repository.save(job);
        runAnalysis(job.getId());
        return job;
    }

    @Async("analysisExecutor")
    public void runAnalysis(UUID jobId) {
        AnalysisJob job = repository.findById(jobId).orElseThrow();
        job.markRunning();
        repository.save(job);

        try {
            Path filePath = documentService.getFilePath(job.getDocument().getId());
            Map<String, Object> result = parserClient.parse(filePath, job.getDocument().getFilename());

            String markdown = (String) result.getOrDefault("content_markdown", "");
            String html = (String) result.getOrDefault("content_html", "");
            Object pages = result.get("pages");
            String pagesJson = pages != null ? objectMapper.writeValueAsString(pages) : "[]";

            // Update page count on document if available
            Object pageCount = result.get("page_count");
            if (pageCount instanceof Number n && n.intValue() > 0) {
                Document doc = job.getDocument();
                doc.setPageCount(n.intValue());
                documentService.save(doc);
            }

            job.markCompleted(markdown, html, pagesJson);
            repository.save(job);

        } catch (Exception e) {
            job.markFailed(e.getMessage());
            repository.save(job);
        }
    }

    public AnalysisJob findById(UUID id) {
        return repository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Analysis not found: " + id));
    }

    public List<AnalysisJob> findAll() {
        return repository.findAllByOrderByCreatedAtDesc();
    }

    public void delete(UUID id) {
        AnalysisJob job = findById(id);
        repository.delete(job);
    }
}
