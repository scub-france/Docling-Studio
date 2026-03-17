package com.docling.studio.document;

import com.docling.studio.shared.exception.ResourceNotFoundException;
import com.docling.studio.shared.exception.ServiceException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.UUID;

@Service
public class DocumentService {

    private final DocumentRepository repository;
    private final DocumentParserClient parserClient;
    private final Path storagePath;

    public DocumentService(
            DocumentRepository repository,
            DocumentParserClient parserClient,
            @Value("${app.storage.path:./uploads}") String storagePath
    ) {
        this.repository = repository;
        this.parserClient = parserClient;
        this.storagePath = Path.of(storagePath);
    }

    public Document upload(MultipartFile file) {
        if (file.isEmpty() || file.getOriginalFilename() == null) {
            throw new IllegalArgumentException("File is empty or has no name");
        }

        try {
            Files.createDirectories(storagePath);
            String safeName = UUID.randomUUID() + "_" + file.getOriginalFilename();
            Path target = storagePath.resolve(safeName);
            file.transferTo(target);

            Document doc = new Document(
                    file.getOriginalFilename(),
                    file.getContentType(),
                    file.getSize(),
                    target.toString()
            );
            return repository.save(doc);

        } catch (IOException e) {
            throw new ServiceException("Failed to store file", e);
        }
    }

    public Document save(Document document) {
        return repository.save(document);
    }

    public List<Document> findAll() {
        return repository.findAll();
    }

    public Document findById(UUID id) {
        return repository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Document not found: " + id));
    }

    public void delete(UUID id) {
        Document doc = findById(id);
        try {
            Files.deleteIfExists(Path.of(doc.getStoragePath()));
        } catch (IOException e) {
            // Log but continue
        }
        repository.delete(doc);
    }

    public byte[] getPreview(UUID id, int page, int dpi) {
        Document doc = findById(id);
        return parserClient.preview(Path.of(doc.getStoragePath()), doc.getFilename(), page, dpi);
    }

    public Path getFilePath(UUID id) {
        Document doc = findById(id);
        return Path.of(doc.getStoragePath());
    }
}
