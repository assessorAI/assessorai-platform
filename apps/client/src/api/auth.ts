import 'server-only'
import { auth } from './auth/index'
import type { Session } from 'next-auth'

export interface VerifiedSession {
  isAuth: boolean
  accessToken: string
  user: {
    email: string
    first_name: string
    last_name: string
    casa_legislativa: string
  }
}

// Função principal para verificar sessão - seguindo padrão DAL
export async function verifySession(): Promise<VerifiedSession | null> {
  const session = await auth()

  if (!session?.user) {
    return null
  }

  type SessionWithToken = Session & {
    accessToken?: string
    user: Session['user'] & { accessToken?: string }
  }

  const sessionWithToken = session as SessionWithToken
  const accessToken = sessionWithToken.accessToken ?? sessionWithToken.user.accessToken ?? ""

  return {
    isAuth: true,
    accessToken,
    user: {
      email: session.user.email!,
      first_name: session.user.first_name!,
      last_name: session.user.last_name!,
      casa_legislativa: session.user.casa_legislativa!
    }
  }
}

// Função para obter usuário autenticado
export async function getUser() {
  const session = await verifySession()

  if (!session) {
    return null
  }

  return session.user
}
