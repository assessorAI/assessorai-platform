"use client";
import styles from "../register/register.module.scss";

import { DadosPessoais } from "./steps/dados-pessoais";
import { CrieSenha } from "./steps/crie-senha";
import { FeedbackEnviado } from "./steps/feedback-enviado";
import { CustomLink } from "@/components/link";
import { RegisterMemberStepProvider, useStep } from "./register-member-step.context";
import { UserResponse } from "@/api/user/user.types";

function RenderRegisterMemberStep({ step }: { step: number }) {
  switch (step) {
    case 1:
      return <DadosPessoais />;
    case 2:
      return <CrieSenha />;
    case 3:
      return <FeedbackEnviado />;
    default:
      return <DadosPessoais />;
  }
}

function RegisterMemberStepContent() {
  const { step } = useStep();
  
  return (
    <>
      <RenderRegisterMemberStep step={step} />
      {step < 3 && (
        <span className={styles.link}>Já tem conta? <CustomLink href="/login">Entrar</CustomLink></span>
      )}
    </>
  );
}

export function RegisterMemberStep({ user }: { user: UserResponse }) {
  return (
    <RegisterMemberStepProvider user={user}>
      <RegisterMemberStepContent />
    </RegisterMemberStepProvider>
  );
}