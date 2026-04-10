import { createContext, useContext, useState } from "react";
import { dadosPessoais } from "../../../types/schemas/dados-pessoais.schema";
import { crieSenha } from "../../../types/schemas/crie-senha.schema";
import { UserResponse } from "@/api/user/user.types";

export type FormDataRegister = dadosPessoais & crieSenha;

type StepContextType = {
  step: number;
  nextStep: () => void;
  prevStep: () => void;
  updateData: (data: Partial<FormDataRegister>) => void;
  formData: Partial<FormDataRegister>;
  userData: UserResponse;
};

const StepContext = createContext<StepContextType | undefined>(undefined);

export function RegisterMemberStepProvider({
  children,
  user,
}: {
  user: UserResponse;
  children: React.ReactNode;
}) {
  const [step, setStep] = useState(1);
  const [userData] = useState(user);
  const [formData, setFormData] = useState<Partial<FormDataRegister>>({});

  const nextStep = () => setStep((s) => s + 1);
  const prevStep = () => setStep((s) => s - 1);

  const updateData = (data: Partial<FormDataRegister>) =>
    setFormData((prev) => ({ ...prev, ...data }));

  return (
    <StepContext.Provider
      value={{ step, nextStep, prevStep, updateData, formData, userData }}
    >
      {children}
    </StepContext.Provider>
  );
}

export function useStep() {
  const context = useContext(StepContext);
  if (!context)
    throw new Error("useStep deve ser usado dentro de StepProvider");
  return context;
}
