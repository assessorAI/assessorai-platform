import type { Metadata } from "next"
import { ResetPassword } from "@/features/auth/reset-password/reset-password"
import AuthTemplate from "@/components/templates/auth/auth"
import { Suspense } from "react"
import { Spinner } from "@/components/ui/spinner"

export const metadata: Metadata = {
  title: "Recuperar senha - Assessor AI",
  description: "Recupere sua senha na plataforma Assessor AI",
}

export default function ResetPasswordPage() {

  const description = (
    <p className="text-2.5xl font-sora font-semibold text-gray-900 leading-[3rem] tracking-[-0.576px]">
      A <span className="text-purple-600">inteligência</span> que<br />
      transforma seu mandato.
    </p>
  )
  return (
    <AuthTemplate description={description}>
      <Suspense fallback={<Spinner />}>
        <ResetPassword />
      </Suspense>
    </AuthTemplate>
  )
} 