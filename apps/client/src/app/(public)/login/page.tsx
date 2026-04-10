import type { Metadata } from "next"
import { LoginForm } from "@/features/auth/login/login"
import AuthTemplate from "@/components/templates/auth/auth"

export const metadata: Metadata = {
  title: "Login - Assessor AI",
  description: "Faça login na plataforma Assessor AI",
}

export default function LoginPage() {

  const description = (
    <p className="text-2.5xl font-sora font-semibold text-gray-900 leading-[3rem] tracking-[-0.576px]">
      A <span className="text-purple-600">inteligência</span> que<br />
      transforma seu mandato.
    </p>
  )
  return <AuthTemplate description={description}><LoginForm /></AuthTemplate>
} 