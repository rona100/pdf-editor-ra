import { useState } from 'react'

type OperationState = 'idle' | 'loading' | 'success' | 'error'

export function useOperation() {
  const [state, setState] = useState<OperationState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [filename, setFilename] = useState<string | null>(null)

  async function execute(
    endpoint: string,
    formData: FormData,
    outputFilename: string
  ) {
    setState('loading')
    setError(null)
    try {
      const res = await fetch(endpoint, { method: 'POST', body: formData })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail ?? `Error: ${res.statusText}`)
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = outputFilename
      a.click()
      URL.revokeObjectURL(url)
      setFilename(outputFilename)
      setState('success')
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      setState('error')
    }
  }

  return { state, error, filename, execute }
}
