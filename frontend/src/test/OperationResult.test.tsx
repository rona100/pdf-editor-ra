import { render, screen } from '@testing-library/react'
import { OperationResult } from '../components/OperationResult'

describe('OperationResult', () => {
  it('renders nothing when idle', () => {
    const { container } = render(
      <OperationResult state="idle" error={null} filename={null} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('shows processing message when loading', () => {
    render(<OperationResult state="loading" error={null} filename={null} />)
    expect(screen.getByText('Processing...')).toBeInTheDocument()
  })

  it('shows error heading and message when error', () => {
    render(
      <OperationResult state="error" error="Something went wrong" filename={null} />
    )
    expect(screen.getByText('Error')).toBeInTheDocument()
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('shows filename in success message', () => {
    render(
      <OperationResult state="success" error={null} filename="rotated.pdf" />
    )
    expect(screen.getByText(/rotated\.pdf/)).toBeInTheDocument()
  })

  it('renders nothing for unknown state', () => {
    const { container } = render(
      // @ts-expect-error testing invalid state
      <OperationResult state="unknown" error={null} filename={null} />
    )
    expect(container.firstChild).toBeNull()
  })
})
