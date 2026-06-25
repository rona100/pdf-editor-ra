import React, { useState } from 'react'
import { RotateOperation } from './operations/RotateOperation'
import { MergeOperation } from './operations/MergeOperation'
import { OrderOperation } from './operations/OrderOperation'
import { ConvertOperation } from './operations/ConvertOperation'
import { FileText } from 'lucide-react'

function App() {
  const [activeTab, setActiveTab] = useState<'rotate' | 'merge' | 'order' | 'convert'>('rotate')

  const tabs = [
    { id: 'rotate', label: 'Rotate Pages', icon: '🔄' },
    { id: 'merge', label: 'Merge PDFs', icon: '📎' },
    { id: 'order', label: 'Reorder Pages', icon: '↕️' },
    { id: 'convert', label: 'Convert to DOCX', icon: '📄' },
  ] as const

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-4xl mx-auto px-6 py-6">
          <div className="flex items-center gap-3 mb-2">
            <FileText className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">PDF Editor</h1>
          </div>
          <p className="text-gray-600">Rotate, merge, reorder, and convert PDF files</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 mb-6">
          <div className="flex border-b border-slate-200">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 px-4 py-4 font-medium text-center transition-colors border-b-2 ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600 bg-blue-50'
                    : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-8">
          {activeTab === 'rotate' && <RotateOperation />}
          {activeTab === 'merge' && <MergeOperation />}
          {activeTab === 'order' && <OrderOperation />}
          {activeTab === 'convert' && <ConvertOperation />}
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-4xl mx-auto px-6 py-8 text-center text-sm text-gray-500 mt-8">
        <p>PDF Editor v0.1.0 • Built with React & FastAPI</p>
      </div>
    </div>
  )
}

export default App
