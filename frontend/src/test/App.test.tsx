import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../App'

describe('App', () => {
  it('renders the app heading', () => {
    render(<App />)
    expect(screen.getByText('PDF Editor')).toBeInTheDocument()
  })

  it('renders all four operation tabs', () => {
    render(<App />)
    expect(screen.getByText('Rotate Pages')).toBeInTheDocument()
    expect(screen.getByText('Merge PDFs')).toBeInTheDocument()
    expect(screen.getByText('Reorder Pages')).toBeInTheDocument()
    expect(screen.getByText('Convert to DOCX')).toBeInTheDocument()
  })

  it('shows the Rotate operation by default', () => {
    render(<App />)
    expect(screen.getByText('Pages to Rotate')).toBeInTheDocument()
    expect(screen.getByText('Rotation Angle')).toBeInTheDocument()
  })

  it('switches to the Merge operation', async () => {
    render(<App />)
    await userEvent.click(screen.getByText('Merge PDFs'))
    expect(screen.getByText('First PDF File')).toBeInTheDocument()
    expect(screen.getByText('Second PDF File')).toBeInTheDocument()
  })

  it('switches to the Reorder operation', async () => {
    render(<App />)
    await userEvent.click(screen.getByText('Reorder Pages'))
    expect(screen.getByText('Number of Pages to Reorder')).toBeInTheDocument()
    expect(screen.getByText('New Order')).toBeInTheDocument()
  })

  it('switches to the Convert operation', async () => {
    render(<App />)
    await userEvent.click(screen.getByText('Convert to DOCX'))
    expect(screen.getByText(/image-based or complex pdfs/i)).toBeInTheDocument()
  })

  it('renders the footer', () => {
    render(<App />)
    expect(screen.getByText(/PDF Editor v0\.1\.0/)).toBeInTheDocument()
  })
})
