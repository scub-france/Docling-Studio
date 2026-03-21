export interface Document {
  id: string
  filename: string
  contentType: string | null
  fileSize: number | null
  pageCount: number | null
  createdAt: string
}

export interface PipelineOptions {
  do_ocr?: boolean
  do_table_structure?: boolean
  table_mode?: 'accurate' | 'fast'
  do_code_enrichment?: boolean
  do_formula_enrichment?: boolean
  do_picture_classification?: boolean
  do_picture_description?: boolean
  generate_picture_images?: boolean
  generate_page_images?: boolean
  images_scale?: number
}

export type AnalysisStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'

export interface Analysis {
  id: string
  documentId: string
  documentFilename: string | null
  status: AnalysisStatus
  contentMarkdown: string | null
  contentHtml: string | null
  pagesJson: string | null
  errorMessage: string | null
  startedAt: string | null
  completedAt: string | null
  createdAt: string
}

export interface PageElement {
  type: string
  bbox: [number, number, number, number]
  content: string
  level: number
}

// Backend serializes with snake_case (dataclasses.asdict)
export interface Page {
  page_number: number
  width: number
  height: number
  elements: PageElement[]
}

export type ElementType =
  | 'title'
  | 'section_header'
  | 'text'
  | 'table'
  | 'picture'
  | 'list'
  | 'formula'
  | 'code'
  | 'caption'
  | 'floating'

export interface Scale {
  sx: number
  sy: number
}

export interface Rect {
  x: number
  y: number
  w: number
  h: number
}

export type Locale = 'fr' | 'en'
export type Theme = 'dark' | 'light'
