import { useSettingsStore } from '../features/settings/store.js'

const messages = {
  fr: {
    // Sidebar
    'nav.studio': 'Studio',
    'nav.history': 'Historique',
    'nav.settings': 'Paramètres',

    // Studio — import
    'studio.title': 'Intelligence des documents',
    'studio.subtitle': 'Importez un document PDF pour commencer l\'analyse avec Docling',
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
    'config.pages': 'Pages',
    'config.pagesPlaceholder': 'par ex. "1-4,8"',
    'config.extractTables': 'Extraire les tableaux',
    'config.markdownIntegrated': 'Markdown intégré',
    'config.extract': 'Extraire',
    'config.images': 'Images',
    'config.header': 'En-tête',
    'config.footer': 'Pied de page',
    'config.annotateImages': 'Annoter les images',
    'config.add': 'Ajouter +',
    'config.documents': 'Documents',

    // Results
    'results.textResult': 'Résultat du texte',
    'results.markdown': 'Markdown',
    'results.images': 'Images',
    'results.pageOf': 'Page {current} sur {total}',
    'results.noImages': 'Aucune image détectée dans ce document',
    'results.noMarkdown': 'Pas de contenu markdown',
    'results.runAnalysis': 'Lancez une analyse pour voir les résultats',
    'results.analysisFailed': 'L\'analyse a échoué',
    'results.page': 'Page',

    // Upload
    'upload.drop': 'Déposez un PDF ici ou cliquez pour importer',
    'upload.uploading': 'Import en cours...',
    'upload.maxSize': 'Max 50Mo',

    // History
    'history.title': 'Historique des analyses',
    'history.empty': 'Aucune analyse. Allez dans Studio pour analyser votre premier document.',

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
    'config.pages': 'Pages',
    'config.pagesPlaceholder': 'e.g. "1-4,8"',
    'config.extractTables': 'Extract tables',
    'config.markdownIntegrated': 'Inline Markdown',
    'config.extract': 'Extract',
    'config.images': 'Images',
    'config.header': 'Header',
    'config.footer': 'Footer',
    'config.annotateImages': 'Annotate images',
    'config.add': 'Add +',
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

    'history.title': 'Analysis History',
    'history.empty': 'No analyses yet. Go to Studio to analyze your first document.',

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
