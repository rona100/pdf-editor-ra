import React, { useState } from 'react'
import { FileDropzone } from '../components/FileDropzone'
import { OperationResult } from '../components/OperationResult'
import { useOperation } from '../hooks/useOperation'

export function SanitizeOperation() {
  const [file, setFile] = useState<File | null>(null)
  const [mode, setMode] = useState<'ocr' | 'basic'>('ocr')
  const [lang, setLang] = useState('eng+heb')
  const { state, error, filename, execute } = useOperation()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)
    formData.append('mode', mode)
    if (mode === 'ocr') formData.append('lang', lang.trim())

    await execute('/api/sanitize', formData, 'sanitized.pdf')
  }

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          PDF File
        </label>
        <FileDropzone onFileSelect={setFile} />
        {file && (
          <p className="mt-2 text-sm text-gray-600">
            Selected: <span className="font-medium">{file.name}</span>
          </p>
        )}
      </div>

      <div>
        <label htmlFor="sanitize-mode" className="block text-sm font-medium text-gray-700 mb-2">
          Mode
        </label>
        <select
          id="sanitize-mode"
          value={mode}
          onChange={(e) => setMode(e.target.value as 'ocr' | 'basic')}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="ocr">Full: rebuild pages as images with OCR</option>
          <option value="basic">Basic: strip metadata, annotations and hidden text</option>
        </select>
      </div>

      {mode === 'ocr' && (
        <div>
          <label htmlFor="ocr-lang" className="block text-sm font-medium text-gray-700 mb-2">
            OCR languages
          </label>
          <input
            id="ocr-lang"
            type="text"
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="mt-2 text-sm text-gray-500">
            Tesseract language codes joined by "+", e.g. eng+heb.
          </p>
        </div>
      )}

      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
        <p className="font-medium">Note:</p>
        {mode === 'ocr' ? (
          <p>
            Every page is rebuilt as an image with a fresh OCR text layer, and the metadata is
            blanked. Hidden text, fonts, annotations and attachments are removed. The text stays
            searchable but is no longer editable, may contain OCR errors, and the file grows.
            OCR takes a few seconds per page.
          </p>
        ) : (
          <p>
            Keeps the original text and fonts. Removes metadata, annotations, form fields,
            invisible text, JavaScript, attachments and links. Text hidden by other means, such
            as white text or text under an image, is not detected.
          </p>
        )}
      </div>

      <button
        onClick={handleSubmit}
        disabled={!file || (mode === 'ocr' && !lang.trim()) || state === 'loading'}
        className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {state === 'loading' ? 'Sanitizing...' : 'Sanitize PDF'}
      </button>

      <OperationResult state={state} error={error} filename={filename} />
    </div>
  )
}
