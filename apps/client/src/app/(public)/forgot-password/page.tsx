import type { Metadata } from "next"
import AuthTemplate from "@/components/templates/auth/auth"
import { ForgotPasswordForm } from "@/features/auth/forgot-password/forgot-password"

export const metadata: Metadata = {
  title: "Login - Assessor AI",
  description: "Recupere sua senha na plataforma Assessor AI",
}

export default function ForgotPasswordPage() {

  const description = (
    <p className="text-2.5xl font-sora font-semibold text-gray-900 leading-[3rem] tracking-[-0.576px]">
      A <span className="text-purple-600">inteligência</span> que<br />
      transforma seu mandato.
    </p>
  )
  return <AuthTemplate description={description}><ForgotPasswordForm /></AuthTemplate>
} 