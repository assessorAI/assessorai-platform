import '@testing-library/jest-dom'

// Mock global do fetch
global.fetch = jest.fn()

// Mock do NextAuth
jest.mock('next-auth/react', () => ({
  signIn: jest.fn(),
  signOut: jest.fn(),
  useSession: jest.fn(() => ({ data: null, status: 'unauthenticated' }))
}))

// Mock do server-only
jest.mock('server-only', () => ({}))

// Suprimir console.error durante testes (opcional)
const originalError = console.error
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    // Suprimir apenas erros esperados do proxy
    if (args[0] === 'Erro no proxy:') {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
}) 