"use client";
import { RegisterStepProvider } from "@/features/auth/register/register-step.context";

import { useStep } from "@/features/auth/register/register-step.context";
import { FeedbackUsuarioCriadoAdm } from "@/components/app-form/feedback-usuario-criado-adm";
import { NovoUsuarioMandatoExistente } from "@/components/app-form/novo-usuario-mandato-existente";
import { userService } from "@/lib/user.service";
import { CrieSenhaOptionsAdmForm } from "@/components/app-form/crie-senha-options-adm-form";

function RenderNovoUsuarioStep({ step }: { step: number }) {
  switch (step) {
    case 1:
      return <NovoUsuarioMandatoExistente />;
    case 2:
      return <CrieSenhaOptionsAdmForm onRegisterCallback={userService.create} />;
    case 3:
      return <FeedbackUsuarioCriadoAdm />;
    default:
      return <NovoUsuarioMandatoExistente />;
  }
}

function NovoUsuarioStepContent() {
  const { step } = useStep();
  
  return (
    <>
      <RenderNovoUsuarioStep step={step} />
    </>
  );
}

export function NovoUsuarioStep() {
  return (
    <RegisterStepProvider totalSteps={2}>
      <NovoUsuarioStepContent />
    </RegisterStepProvider>
  );
}