"use client";
import { RegisterStepProvider } from "@/features/auth/register/register-step.context";

import { DadosPessoais } from "@/components/app-form/dados-pessoais";
import { DadosMandato } from "@/components/app-form/dados-mandato";
import { PerfilMandato } from "@/components/app-form/perfil-mandato";
import { useStep } from "@/features/auth/register/register-step.context";
import { FeedbackMandatoCriadoAdm } from "@/components/app-form/feedback-mandato-criado-adm";
import { CrieSenhaOptionsAdmForm } from "@/components/app-form/crie-senha-options-adm-form";
import { registerService } from "@/lib/register.service";

function RenderNovoMandatoStep({ step }: { step: number }) {
  switch (step) {
    case 1:
      return <DadosPessoais />;
    case 2:
      return <DadosMandato />;
    case 3:
      return <PerfilMandato />;
    case 4:
      return <CrieSenhaOptionsAdmForm onRegisterCallback={registerService.register} />;
    case 5:
      return <FeedbackMandatoCriadoAdm />;
    default:
      return <DadosPessoais />;
  }
}

function NovoMandatoStepContent() {
  const { step } = useStep();
  
  return (
    <>
      <RenderNovoMandatoStep step={step} />
    </>
  );
}

export function NovoMandatoStep() {
  return (
    <RegisterStepProvider totalSteps={4}>
      <NovoMandatoStepContent />
    </RegisterStepProvider>
  );
}