import { renderHook, act } from '@testing-library/react'
import { useOperation } from '../hooks/useOperation'

describe('useOperation', () => {
  beforeEach(() => {
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-url')
    vi.spyOn(URL, 'revokeObjectURL').mockReturnValue(undefined)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('starts in idle state with no error or filename', () => {
    const { result } = renderHook(() => useOperation())
    expect(result.current.state).toBe('idle')
    expect(result.current.error).toBeNull()
    expect(result.current.filename).toBeNull()
  })

  it('transitions idle → success on a successful fetch', async () => {
    const mockBlob = new Blob(['pdf bytes'], { type: 'application/pdf' })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
    }))

    const { result } = renderHook(() => useOperation())

    await act(async () => {
      await result.current.execute('/api/rotate', new FormData(), 'rotated.pdf')
    })

    expect(result.current.state).toBe('success')
    expect(result.current.filename).toBe('rotated.pdf')
    expect(result.current.error).toBeNull()
  })

  it('transitions idle → error when the server returns a non-ok response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({ detail: 'PDF processing failed' }),
    }))

    const { result } = renderHook(() => useOperation())

    await act(async () => {
      await result.current.execute('/api/rotate', new FormData(), 'rotated.pdf')
    })

    expect(result.current.state).toBe('error')
    expect(result.current.error).toBe('PDF processing failed')
    expect(result.current.filename).toBeNull()
  })

  it('falls back to statusText when response body has no detail field', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      statusText: 'Bad Request',
      json: () => Promise.resolve({}),
    }))

    const { result } = renderHook(() => useOperation())

    await act(async () => {
      await result.current.execute('/api/rotate', new FormData(), 'rotated.pdf')
    })

    expect(result.current.state).toBe('error')
    expect(result.current.error).toBe('Error: Bad Request')
  })

  it('transitions idle → error when fetch throws a network error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')))

    const { result } = renderHook(() => useOperation())

    await act(async () => {
      await result.current.execute('/api/rotate', new FormData(), 'rotated.pdf')
    })

    expect(result.current.state).toBe('error')
    expect(result.current.error).toBe('Network error')
  })

  it('calls URL.createObjectURL and revokeObjectURL on success', async () => {
    const mockBlob = new Blob(['pdf'], { type: 'application/pdf' })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
    }))

    const { result } = renderHook(() => useOperation())

    await act(async () => {
      await result.current.execute('/api/merge', new FormData(), 'merged.pdf')
    })

    expect(URL.createObjectURL).toHaveBeenCalledWith(mockBlob)
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
  })
})
