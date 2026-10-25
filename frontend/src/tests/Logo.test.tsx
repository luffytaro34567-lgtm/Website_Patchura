import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Logo } from '@/components/shared/Logo'

describe('Logo Component', () => {
  it('renders horizontal variant with full PATCHORA wordmark', () => {
    render(<Logo variant="horizontal" size="md" />)
    const logo = screen.getByRole('img', { name: /PATCHORA logo/i })
    expect(logo).toBeInTheDocument()
    expect(logo.textContent).toContain('PATCH')
    expect(logo.textContent).toContain('ORA')
  })

  it('renders symbol-only variant without text wordmark', () => {
    render(<Logo variant="symbol" size="sm" />)
    const logo = screen.getByRole('img', { name: /PATCHORA logo/i })
    expect(logo).toBeInTheDocument()
    expect(logo.textContent).not.toContain('PATCH')
  })

  it('supports explicit dark and light theme styles', () => {
    const { rerender } = render(<Logo variant="horizontal" logoTheme="dark" />)
    expect(screen.getByRole('img')).toBeInTheDocument()

    rerender(<Logo variant="horizontal" logoTheme="light" />)
    expect(screen.getByRole('img')).toBeInTheDocument()

    rerender(<Logo variant="horizontal" logoTheme="monochrome" />)
    expect(screen.getByRole('img')).toBeInTheDocument()
  })

  it('applies custom dimensions and classNames gracefully', () => {
    render(<Logo variant="symbol" size="xl" className="custom-test-class" />)
    const logo = screen.getByRole('img')
    expect(logo).toHaveClass('custom-test-class')
    expect(logo).toHaveAttribute('height', '48')
  })
})
