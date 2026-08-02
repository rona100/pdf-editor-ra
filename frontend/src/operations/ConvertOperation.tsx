import React, { useState } from 'react'
import { FileDropzone } from '../components/FileDropzone'
import { OperationResult } from '../components/OperationResult'
import { useOperation } from '../hooks/useOperation'

export function ConvertOperation() {
  const [file, setFile] = useState<File | null>(null)
  const [rtl, setRtl] = useState<'auto' | 'on' | 'off'>('auto')
  const { state, error, filename, execute } = useOperation()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)
    formData.append('rtl', rtl)

    await execute('/api/convert', formData, 'converted.docx')
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
        <label htmlFor="rtl-mode" className="block text-sm font-medium text-gray-700 mb-2">
          Right-to-left text (Hebrew, Arabic)
        </label>
        <select
          id="rtl-mode"
          value={rtl}
          onChange={(e) => setRtl(e.target.value as 'auto' | 'on' | 'off')}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="auto">Detect automatically</option>
          <option value="on">Always repair</option>
          <option value="off">Never repair</option>
        </select>
        <p className="mt-2 text-sm text-gray-500">
          Repairs word order and marks the document right-to-left. Left-to-right PDFs are unaffected.
        </p>
      </div>

      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
        <p className="font-medium">Note:</p>
        <p>
          The conversion preserves text and formatting. Image-based or complex PDFs may have lower quality.
        </p>
      </div>

      <button
        onClick={handleSubmit}
        disabled={!file || state === 'loading'}
        className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {state === 'loading' ? 'Converting...' : 'Convert to DOCX'}
      </button>

      <OperationResult state={state} error={error} filename={filename} />
    </div>
  )
}
