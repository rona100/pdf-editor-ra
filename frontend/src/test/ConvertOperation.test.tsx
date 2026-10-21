import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ConvertOperation } from '../operations/ConvertOperation'

function makePdfFile() {
  return new File(['%PDF-1.4'], 'document.pdf', { type: 'application/pdf' })
}

async function submitWith(rtl?: string) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    blob: async () => new Blob(['docx bytes']),
  })
  vi.stubGlobal('fetch', fetchMock)

  const { container } = render(<ConvertOperation />)
  const input = container.querySelector('input[type="file"]') as HTMLInputElement
  await userEvent.upload(input, makePdfFile())

  if (rtl) {
    await userEvent.selectOptions(screen.getByLabelText(/right-to-left text/i), rtl)
  }
  await userEvent.click(screen.getByRole('button', { name: 'Convert to DOCX' }))

  await waitFor(() => expect(fetchMock).toHaveBeenCalled())
  return fetchMock.mock.calls[0][1].body as FormData
}

describe('ConvertOperation', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('defaults the RTL mode to automatic detection', () => {
    render(<ConvertOperation />)
    expect(screen.getByLabelText(/right-to-left text/i)).toHaveValue('auto')
  })

  it('sends the default RTL mode with the upload', async () => {
    expect((await submitWith()).get('rtl')).toBe('auto')
  })

  it('sends "on" when the user forces the repair pass', async () => {
    expect((await submitWith('on')).get('rtl')).toBe('on')
  })

  it('sends "off" when the user disables the repair pass', async () => {
    expect((await submitWith('off')).get('rtl')).toBe('off')
  })
})
