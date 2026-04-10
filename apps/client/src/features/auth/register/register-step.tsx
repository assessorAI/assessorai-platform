"use client";
import styles from "./register.module.scss";

import { RegisterStepProvider, useStep } from "./register-step.context";
import { DadosPessoais } from "@/components/app-form/dados-pessoais";
import { DadosMandato } from "@/components/app-form/dados-mandato";
import { PerfilMandato } from "@/components/app-form/perfil-mandato";
import { CrieSenha } from "@/components/app-form/crie-senha";
import { FeedbackCadastroEnviado } from "@/components/app-form/feedback-cadastro-enviado";
import { CustomLink } from "@/components/link";

function RenderRegisterStep({ step }: { step: number }) {
  switch (step) {
    case 1:
      return <DadosPessoais />;
    case 2:
      return <DadosMandato />;
    case 3:
      return <PerfilMandato />;
    case 4:
      return <CrieSenha />;
    case 5:
      return <FeedbackCadastroEnviado />;
    default:
      return <DadosPessoais />;
  }
}

function RegisterStepContent() {
  const { step } = useStep();
  
  return (
    <>
      <RenderRegisterStep step={step} />
      {step < 5 && (
        <span className={styles.link}>Já tem conta? <CustomLink href="/login">Entrar</CustomLink></span>
      )}
    </>
  );
}

export function RegisterStep() {
  return (
    <RegisterStepProvider totalSteps={4}>
      <RegisterStepContent />
    </RegisterStepProvider>
  );
}