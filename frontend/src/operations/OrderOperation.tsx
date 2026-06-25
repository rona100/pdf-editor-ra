import React, { useState } from 'react'
import { FileDropzone } from '../components/FileDropzone'
import { OperationResult } from '../components/OperationResult'
import { useOperation } from '../hooks/useOperation'

export function OrderOperation() {
  const [file, setFile] = useState<File | null>(null)
  const [numPages, setNumPages] = useState('')
  const [newOrder, setNewOrder] = useState('')
  const { state, error, filename, execute } = useOperation()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || !numPages || !newOrder) return

    const formData = new FormData()
    formData.append('file', file)
    formData.append('num_pages', numPages)
    formData.append('new_order', newOrder)

    await execute('/api/order', formData, 'ordered.pdf')
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

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Number of Pages to Reorder
          </label>
          <input
            type="number"
            value={numPages}
            onChange={(e) => setNumPages(e.target.value)}
            placeholder="e.g., 6"
            min="1"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            New Order
          </label>
          <input
            type="text"
            value={newOrder}
            onChange={(e) => setNewOrder(e.target.value)}
            placeholder="e.g., 1,3,2,5,4,6"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
        <p className="font-medium mb-1">Example:</p>
        <p>Position 1 gets page 1, position 2 gets page 3, position 3 gets page 2, etc.</p>
      </div>

      <button
        onClick={handleSubmit}
        disabled={!file || !numPages || !newOrder || state === 'loading'}
        className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {state === 'loading' ? 'Reordering...' : 'Reorder Pages'}
      </button>

      <OperationResult state={state} error={error} filename={filename} />
    </div>
  )
}
