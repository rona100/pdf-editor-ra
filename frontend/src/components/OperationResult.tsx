import React from 'react'
import { AlertCircle, CheckCircle, Loader } from 'lucide-react'

interface OperationResultProps {
  state: 'idle' | 'loading' | 'success' | 'error'
  error: string | null
  filename: string | null
}

export function OperationResult({ state, error, filename }: OperationResultProps) {
  if (state === 'idle') return null

  if (state === 'loading') {
    return (
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center">
        <Loader className="w-5 h-5 text-blue-600 animate-spin mr-3" />
        <span className="text-blue-700">Processing...</span>
      </div>
    )
  }

  if (state === 'error') {
    return (
      <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
        <AlertCircle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
        <div className="text-red-700">
          <p className="font-medium">Error</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    )
  }

  if (state === 'success') {
    return (
      <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center">
        <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
        <span className="text-green-700">
          ✓ Successfully downloaded <span className="font-medium">{filename}</span>
        </span>
      </div>
    )
  }

  return null
}
