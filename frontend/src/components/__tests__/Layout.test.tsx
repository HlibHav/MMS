import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from '../Layout'

describe('Layout', () => {
  it('renders title', () => {
    const client = new QueryClient()
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <Layout><div>content</div></Layout>
        </MemoryRouter>
      </QueryClientProvider>
    )
    expect(screen.getByText('Promo Scenario Co-Pilot')).toBeInTheDocument()
  })
})

