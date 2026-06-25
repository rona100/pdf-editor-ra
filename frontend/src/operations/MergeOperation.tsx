import React, { useState } from 'react'
import { FileDropzone } from '../components/FileDropzone'
import { OperationResult } from '../components/OperationResult'
import { useOperation } from '../hooks/useOperation'

export function MergeOperation() {
  const [file1, setFile1] = useState<File | null>(null)
  const [file2, setFile2] = useState<File | null>(null)
  const { state, error, filename, execute } = useOperation()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file1 || !file2) return

    const formData = new FormData()
    formData.append('file1', file1)
    formData.append('file2', file2)

    await execute('/api/merge', formData, 'merged.pdf')
  }

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          First PDF File
        </label>
        <FileDropzone onFileSelect={setFile1} />
        {file1 && (
          <p className="mt-2 text-sm text-gray-600">
            Selected: <span className="font-medium">{file1.name}</span>
          </p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Second PDF File
        </label>
        <FileDropzone onFileSelect={setFile2} />
        {file2 && (
          <p className="mt-2 text-sm text-gray-600">
            Selected: <span className="font-medium">{file2.name}</span>
          </p>
        )}
      </div>

      <button
        onClick={handleSubmit}
        disabled={!file1 || !file2 || state === 'loading'}
        className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {state === 'loading' ? 'Merging...' : 'Merge PDFs'}
      </button>

      <OperationResult state={state} error={error} filename={filename} />
    </div>
  )
}
