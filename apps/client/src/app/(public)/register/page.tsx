import type { Metadata } from "next";
import { RegisterStep } from "@/features/auth/register/register-step";
import AuthTemplate from "@/components/templates/auth/auth";

export const metadata: Metadata = {
  title: "Cadastro - Assessor AI",
  description: "Crie sua conta na plataforma Assessor AI",
};

export default function RegisterPage() {
  const description = (
    <header className="space-y-5">
    <h1>
      Cadastre seu mandato
    </h1>

    <p className="text-gray-500 text-lg max-w-sm">
      Crie uma conta para o seu mandato e convide membros da sua equipe para utilizar a plataforma com você.
    </p>
    </header>
  );
  return <AuthTemplate description={description}><RegisterStep /></AuthTemplate>
}
