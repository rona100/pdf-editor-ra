import React, { useState } from 'react'
import { FileDropzone } from '../components/FileDropzone'
import { OperationResult } from '../components/OperationResult'
import { useOperation } from '../hooks/useOperation'

const DOCX_ACCEPT =
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx'

export function Docx2PdfOperation() {
  const [file, setFile] = useState<File | null>(null)
  const { state, error, filename, execute } = useOperation()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    await execute('/api/docx2pdf', formData, 'converted.pdf')
  }

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          DOCX File
        </label>
        <FileDropzone
          onFileSelect={setFile}
          accept={DOCX_ACCEPT}
          prompt="Drop your DOCX here or click to browse"
        />
        {file && (
          <p className="mt-2 text-sm text-gray-600">
            Selected: <span className="font-medium">{file.name}</span>
          </p>
        )}
      </div>

      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
        <p className="font-medium">Note:</p>
        <p>
          Conversion runs through LibreOffice on the server. Layout, tables, images, and
          right-to-left text are preserved.
        </p>
      </div>

      <button
        onClick={handleSubmit}
        disabled={!file || state === 'loading'}
        className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {state === 'loading' ? 'Converting...' : 'Convert to PDF'}
      </button>

      <OperationResult state={state} error={error} filename={filename} />
    </div>
  )
}
