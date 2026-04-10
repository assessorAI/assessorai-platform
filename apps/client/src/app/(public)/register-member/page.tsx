import type { Metadata } from "next";

import AuthTemplate from "@/components/templates/auth/auth";
import { RegisterMemberStep } from "@/features/auth/register-member/register-member-step";
import { userService } from "@/api/user/user.service";

export const metadata: Metadata = {
  title: "Cadastro - Assessor AI",
  description: "Crie sua conta na plataforma Assessor AI",
};

export default async function RegisterMemberPage({ searchParams }: { searchParams: Promise<{ token: string }> }) {
  const { token } = await searchParams;

  const user = await userService.getUserByToken(token as string);
  
  const description = (
    <header className="space-y-5">
    <h1>
      Cadastre seu usuário
    </h1>

    <p className="text-gray-500 text-lg max-w-sm">
    Você recebeu um convite para fazer parte de uma equipe de um mandato. 
    Cadastre seus dados para utilizar a plataforma.
    </p>
    </header>
  );
  return <AuthTemplate description={description}><RegisterMemberStep user={user} /></AuthTemplate>
}
