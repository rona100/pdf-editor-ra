import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FileDropzone } from '../components/FileDropzone'

describe('FileDropzone', () => {
  it('renders the drop area prompt', () => {
    render(<FileDropzone onFileSelect={() => {}} />)
    expect(screen.getByText(/Drop your PDF here/)).toBeInTheDocument()
  })

  it('has a hidden file input with the default pdf accept type', () => {
    const { container } = render(<FileDropzone onFileSelect={() => {}} />)
    const input = container.querySelector('input[type="file"]')
    expect(input).toBeInTheDocument()
    expect(input).toHaveAttribute('accept', 'application/pdf')
  })

  it('uses a custom accept prop when provided', () => {
    const { container } = render(<FileDropzone onFileSelect={() => {}} accept=".docx" />)
    const input = container.querySelector('input[type="file"]')
    expect(input).toHaveAttribute('accept', '.docx')
  })

  it('calls onFileSelect when a file is dropped', () => {
    const onFileSelect = vi.fn()
    render(<FileDropzone onFileSelect={onFileSelect} />)
    const dropzone = screen.getByText(/Drop your PDF here/).closest('div')!
    const file = new File(['pdf content'], 'document.pdf', { type: 'application/pdf' })

    fireEvent.drop(dropzone, { dataTransfer: { files: [file] } })

    expect(onFileSelect).toHaveBeenCalledOnce()
    expect(onFileSelect).toHaveBeenCalledWith(file)
  })

  it('calls onFileSelect when a file is chosen via the input', async () => {
    const onFileSelect = vi.fn()
    const { container } = render(<FileDropzone onFileSelect={onFileSelect} />)
    const input = container.querySelector('input[type="file"]')!
    const file = new File(['pdf content'], 'document.pdf', { type: 'application/pdf' })

    await userEvent.upload(input, file)

    expect(onFileSelect).toHaveBeenCalledOnce()
    expect(onFileSelect).toHaveBeenCalledWith(file)
  })

  it('does not call onFileSelect when drop has no files', () => {
    const onFileSelect = vi.fn()
    render(<FileDropzone onFileSelect={onFileSelect} />)
    const dropzone = screen.getByText(/Drop your PDF here/).closest('div')!

    fireEvent.drop(dropzone, { dataTransfer: { files: [] } })

    expect(onFileSelect).not.toHaveBeenCalled()
  })
})
