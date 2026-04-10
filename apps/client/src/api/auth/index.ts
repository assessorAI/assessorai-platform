import { isExpiredDate } from "@/lib/is-expired-date"
import NextAuth from "next-auth"
import Credentials from "next-auth/providers/credentials"


/**
 * Função principal para autenticação
 * @returns {Object} - Objeto com handlers, signIn, signOut e auth
 * @property {Function} handlers - Função para lidar com as requisições
 * @property {Function} signIn - Função para fazer login
 * @property {Function} signOut - Função para fazer logout
 * @property {Function} auth - Função para verificar a sessão
 */
export const { handlers, signIn, signOut, auth } = NextAuth({
  trustHost: true,
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {

        const res = await fetch(`${process.env.BACKEND_ASSESSORAI_URL}/auth/token`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json" },
          body: new URLSearchParams({
            username: credentials?.email as string,
            password: credentials?.password as string,
          }),
        })

        if (!res.ok) return null
        const data = await res.json()

        const userData = await fetch(`${process.env.BACKEND_ASSESSORAI_URL}/auth/me`, {
          headers: {
            "Content-Type": "application/json",
            "Authorization": `${data.token_type} ${data.access_token}`
          }
        })

        const user = await userData.json()

        if (!userData.ok) return null

        return {
          ...user,
          accessToken: data.access_token,
          expiresAt: data.expiration_date,
        }
      },
    }),
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user, trigger, session }) {
      if (user) {
        Object.assign(token, user);
      }
  
      if (trigger === "update" && session?.user) {
        token = {
          ...token,
          ...session.user,
        };
      }

      if (isExpiredDate(token.expiresAt as string)) {
        return null
      }
  
      return token;
    },
    async session({ session, token }) {
      
      if (session.user) {
        Object.assign(session.user, token)
      }

    if (typeof token.accessToken === 'string') {
      session.accessToken = token.accessToken
    }

    if (token.expiresAt) {
      session.expiresAt = token.expiresAt as string;
    }
      return session
    },
  },
  pages: {
    signIn: "/login",
    signOut: "/login",
  },
})
