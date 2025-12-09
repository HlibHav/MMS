import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Layout from '../Layout'

describe('Layout', () => {
  it('renders title', () => {
    render(
      <MemoryRouter>
        <Layout><div>content</div></Layout>
      </MemoryRouter>
    )
    expect(screen.getByText('Promo Scenario Co-Pilot')).toBeInTheDocument()
  })
})

