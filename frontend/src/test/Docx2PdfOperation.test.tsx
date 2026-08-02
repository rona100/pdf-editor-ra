import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Docx2PdfOperation } from '../operations/Docx2PdfOperation'

const DOCX_TYPE =
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

function makeDocxFile() {
  return new File(['fake docx bytes'], 'report.docx', { type: DOCX_TYPE })
}

describe('Docx2PdfOperation', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('disables the button until a file is chosen', () => {
    render(<Docx2PdfOperation />)
    expect(screen.getByRole('button', { name: 'Convert to PDF' })).toBeDisabled()
  })

  it('accepts DOCX files in the dropzone', () => {
    const { container } = render(<Docx2PdfOperation />)
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    expect(input.accept).toContain('.docx')
  })

  it('shows the selected filename and enables the button', async () => {
    const { container } = render(<Docx2PdfOperation />)
    const input = container.querySelector('input[type="file"]') as HTMLInputElement

    await userEvent.upload(input, makeDocxFile())

    expect(screen.getByText('report.docx')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Convert to PDF' })).toBeEnabled()
  })

  it('posts the file to /api/docx2pdf', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(['%PDF-1.4'], { type: 'application/pdf' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const { container } = render(<Docx2PdfOperation />)
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    await userEvent.upload(input, makeDocxFile())
    await userEvent.click(screen.getByRole('button', { name: 'Convert to PDF' }))

    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    const [endpoint, options] = fetchMock.mock.calls[0]
    expect(endpoint).toBe('/api/docx2pdf')
    expect(options.method).toBe('POST')
    expect((options.body as FormData).get('file')).toBeInstanceOf(File)
  })

  it('surfaces the server error message', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
        json: async () => ({ detail: 'LibreOffice is required' }),
      })
    )

    const { container } = render(<Docx2PdfOperation />)
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    await userEvent.upload(input, makeDocxFile())
    await userEvent.click(screen.getByRole('button', { name: 'Convert to PDF' }))

    expect(await screen.findByText(/LibreOffice is required/)).toBeInTheDocument()
  })
})
