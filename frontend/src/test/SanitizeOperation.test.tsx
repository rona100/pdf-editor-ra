import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SanitizeOperation } from '../operations/SanitizeOperation'

function makePdfFile() {
  return new File(['%PDF-1.4'], 'report.pdf', { type: 'application/pdf' })
}

describe('SanitizeOperation', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('disables the button until a file is chosen', () => {
    render(<SanitizeOperation />)
    expect(screen.getByRole('button', { name: 'Sanitize PDF' })).toBeDisabled()
  })

  it('defaults the OCR languages to eng+heb', () => {
    render(<SanitizeOperation />)
    expect(screen.getByLabelText('OCR languages')).toHaveValue('eng+heb')
  })

  it('posts the file and languages to /api/sanitize', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(['%PDF-1.4'], { type: 'application/pdf' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const { container } = render(<SanitizeOperation />)
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    await userEvent.upload(input, makePdfFile())
    const langInput = screen.getByLabelText('OCR languages')
    await userEvent.clear(langInput)
    await userEvent.type(langInput, 'eng')
    await userEvent.click(screen.getByRole('button', { name: 'Sanitize PDF' }))

    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    const [endpoint, options] = fetchMock.mock.calls[0]
    expect(endpoint).toBe('/api/sanitize')
    expect(options.method).toBe('POST')
    const body = options.body as FormData
    expect(body.get('file')).toBeInstanceOf(File)
    expect(body.get('mode')).toBe('ocr')
    expect(body.get('lang')).toBe('eng')
  })

  it('sends ats mode without a language and explains the trade-off', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(['%PDF-1.4'], { type: 'application/pdf' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const { container } = render(<SanitizeOperation />)
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    await userEvent.upload(input, makePdfFile())
    await userEvent.selectOptions(screen.getByLabelText('Mode'), 'ats')
    expect(screen.queryByLabelText('OCR languages')).not.toBeInTheDocument()
    expect(screen.getByText(/applicant tracking systems/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Sanitize PDF' }))

    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    const body = fetchMock.mock.calls[0][1].body as FormData
    expect(body.get('mode')).toBe('ats')
    expect(body.get('lang')).toBeNull()
  })

  it('sends basic mode without a language and hides the language field', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(['%PDF-1.4'], { type: 'application/pdf' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const { container } = render(<SanitizeOperation />)
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    await userEvent.upload(input, makePdfFile())
    await userEvent.selectOptions(screen.getByLabelText('Mode'), 'basic')
    expect(screen.queryByLabelText('OCR languages')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Sanitize PDF' }))

    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    const body = fetchMock.mock.calls[0][1].body as FormData
    expect(body.get('mode')).toBe('basic')
    expect(body.get('lang')).toBeNull()
  })

  it('surfaces the server error message', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
        json: async () => ({ detail: 'Tesseract is required' }),
      })
    )

    const { container } = render(<SanitizeOperation />)
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    await userEvent.upload(input, makePdfFile())
    await userEvent.click(screen.getByRole('button', { name: 'Sanitize PDF' }))

    expect(await screen.findByText(/Tesseract is required/)).toBeInTheDocument()
  })
})
