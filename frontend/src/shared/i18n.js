import { useSettingsStore } from '../features/settings/store.js'

const messages = {
  fr: {
    // Sidebar
    'nav.studio': 'Studio',
    'nav.history': 'Historique',
    'nav.settings': 'Paramètres',

    // Studio — import
    'studio.title': 'Intelligence des documents',
    'studio.subtitle': "Importez un document PDF pour commencer l'analyse avec Docling",
    'studio.recentDocs': 'Documents récents',

    // Studio — workspace
    'studio.configure': 'Configurer',
    'studio.verify': 'Vérifier',
    'studio.addFiles': 'Ajouter des fichiers',
    'studio.analyzing': 'Analyse...',
    'studio.run': 'Exécuter',
    'studio.loaded': 'Chargé',
    'studio.analysisRunning': 'Analyse en cours...',
    'studio.failed': 'Échec',
    'studio.visual': 'Visuel',

    // Config panel
    'config.model': 'Modèle',
    'config.pipeline': 'Pipeline',
    'config.ocr': 'OCR',
    'config.ocrHint': "Applique la reconnaissance optique de caractères sur les pages scannées ou les images intégrées. Indispensable pour les PDF non-natifs.",
    'config.tableStructure': 'Extraction des tableaux',
    'config.tableStructureHint': "Détecte les tableaux dans le document et reconstruit leur structure lignes/colonnes via le modèle TableFormer, avec correspondance des cellules.",
    'config.tableMode': 'Mode tableaux',
    'config.tableModeAccurate': 'Précis',
    'config.tableModeFast': 'Rapide',
    'config.enrichment': 'Enrichissement',
    'config.codeEnrichment': 'Code',
    'config.codeEnrichmentHint': "Active un modèle OCR spécialisé pour les blocs de code, préservant l'indentation et la syntaxe.",
    'config.formulaEnrichment': 'Formules',
    'config.formulaEnrichmentHint': "Reconnaît les formules mathématiques et les convertit en LaTeX via un modèle dédié.",
    'config.pictures': 'Images',
    'config.pictureClassification': 'Classification',
    'config.pictureClassificationHint': "Classe chaque image détectée par type (graphique, photo, diagramme, logo…) via un modèle de classification.",
    'config.pictureDescription': 'Description',
    'config.pictureDescriptionHint': "Génère une description textuelle de chaque image via un Vision Language Model (VLM). Utile pour l'accessibilité et l'indexation.",
    'config.generatePictureImages': 'Extraire les images',
    'config.generatePictureImagesHint': "Extrait les images détectées du document et les sauvegarde en tant que fichiers séparés. Nécessaire pour l'export d'images.",
    'config.generatePageImages': 'Images de pages',
    'config.generatePageImagesHint': "Rasterise chaque page du PDF en image. Utile pour la visualisation ou le post-traitement visuel.",
    'config.imagesScale': 'Échelle images',
    'config.documents': 'Documents',

    // Results
    'results.textResult': 'Résultat du texte',
    'results.markdown': 'Markdown',
    'results.images': 'Images',
    'results.pageOf': 'Page {current} sur {total}',
    'results.noImages': 'Aucune image détectée dans ce document',
    'results.noMarkdown': 'Pas de contenu markdown',
    'results.runAnalysis': 'Lancez une analyse pour voir les résultats',
    'results.analysisFailed': "L'analyse a échoué",
    'results.page': 'Page',

    // Upload
    'upload.drop': 'Déposez un PDF ici ou cliquez pour importer',
    'upload.uploading': 'Import en cours...',
    'upload.maxSize': 'Max 50Mo',

    // History
    'history.title': 'Historique',
    'history.tabAnalyses': 'Analyses',
    'history.tabDocuments': 'Documents',
    'history.empty': 'Aucune analyse. Allez dans Studio pour analyser votre premier document.',
    'history.emptyDocs': 'Aucun document. Importez un document depuis le Studio.',
    'history.open': 'Ouvrir',

    // Settings
    'settings.title': 'Paramètres',
    'settings.apiUrl': 'API URL',
    'settings.version': 'Version',
    'settings.theme': 'Thème',
    'settings.themeDark': 'Sombre',
    'settings.themeLight': 'Clair',
    'settings.language': 'Langue',
  },
  en: {
    'nav.studio': 'Studio',
    'nav.history': 'History',
    'nav.settings': 'Settings',

    'studio.title': 'Document Intelligence',
    'studio.subtitle': 'Upload a PDF document to start analyzing with Docling',
    'studio.recentDocs': 'Recent documents',

    'studio.configure': 'Configure',
    'studio.verify': 'Verify',
    'studio.addFiles': 'Add files',
    'studio.analyzing': 'Analyzing...',
    'studio.run': 'Run',
    'studio.loaded': 'Loaded',
    'studio.analysisRunning': 'Analysis running...',
    'studio.failed': 'Failed',
    'studio.visual': 'Visual',

    'config.model': 'Model',
    'config.pipeline': 'Pipeline',
    'config.ocr': 'OCR',
    'config.ocrHint': 'Applies Optical Character Recognition on scanned pages or embedded images. Essential for non-native PDFs.',
    'config.tableStructure': 'Table extraction',
    'config.tableStructureHint': 'Detects tables in the document and reconstructs their row/column structure using the TableFormer model, with cell matching.',
    'config.tableMode': 'Table mode',
    'config.tableModeAccurate': 'Accurate',
    'config.tableModeFast': 'Fast',
    'config.enrichment': 'Enrichment',
    'config.codeEnrichment': 'Code',
    'config.codeEnrichmentHint': 'Activates a specialized OCR model for code blocks, preserving indentation and syntax.',
    'config.formulaEnrichment': 'Formulas',
    'config.formulaEnrichmentHint': 'Recognizes mathematical formulas and converts them to LaTeX using a dedicated model.',
    'config.pictures': 'Pictures',
    'config.pictureClassification': 'Classification',
    'config.pictureClassificationHint': 'Classifies each detected image by type (chart, photo, diagram, logo…) using a classification model.',
    'config.pictureDescription': 'Description',
    'config.pictureDescriptionHint': 'Generates a text description for each image using a Vision Language Model (VLM). Useful for accessibility and indexing.',
    'config.generatePictureImages': 'Extract pictures',
    'config.generatePictureImagesHint': 'Extracts detected images from the document and saves them as separate files. Required for image export.',
    'config.generatePageImages': 'Page images',
    'config.generatePageImagesHint': 'Rasterizes each PDF page as an image. Useful for visual preview or post-processing.',
    'config.imagesScale': 'Images scale',
    'config.documents': 'Documents',

    'results.textResult': 'Text result',
    'results.markdown': 'Markdown',
    'results.images': 'Images',
    'results.pageOf': 'Page {current} of {total}',
    'results.noImages': 'No images detected in this document',
    'results.noMarkdown': 'No markdown content',
    'results.runAnalysis': 'Run an analysis to see results',
    'results.analysisFailed': 'Analysis failed',
    'results.page': 'Page',

    'upload.drop': 'Drop a PDF here or click to upload',
    'upload.uploading': 'Uploading...',
    'upload.maxSize': 'Max 50MB',

    'history.title': 'History',
    'history.tabAnalyses': 'Analyses',
    'history.tabDocuments': 'Documents',
    'history.empty': 'No analyses yet. Go to Studio to analyze your first document.',
    'history.emptyDocs': 'No documents yet. Upload a document from the Studio.',
    'history.open': 'Open',

    'settings.title': 'Settings',
    'settings.apiUrl': 'API URL',
    'settings.version': 'Version',
    'settings.theme': 'Theme',
    'settings.themeDark': 'Dark',
    'settings.themeLight': 'Light',
    'settings.language': 'Language',
  }
}

export function useI18n() {
  const settings = useSettingsStore()

  function t(key, params = {}) {
    let str = messages[settings.locale]?.[key] || messages['fr'][key] || key
    for (const [k, v] of Object.entries(params)) {
      str = str.replace(`{${k}}`, v)
    }
    return str
  }

  return { t }
}
