import { createContext, useContext, useState, ReactNode } from "react";

type StepContextType<TFormData> = {
  step: number;
  nextStep: () => void;
  prevStep: () => void;
  updateData: (data: Partial<TFormData>) => void;
  formData: Partial<TFormData>;
  totalSteps: number;
};

function createStepContext<TFormData>() {
  const StepContext = createContext<StepContextType<TFormData> | undefined>(undefined);

  function StepProvider({ children, totalSteps }: { children: ReactNode, totalSteps: number }) {
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState<Partial<TFormData>>({});

    const nextStep = () => setStep((s) => s + 1);
    const prevStep = () => setStep((s) => s - 1);

    const updateData = (data: Partial<TFormData>) =>
      setFormData((prev) => ({ ...prev, ...data }));

    return (
      <StepContext.Provider
        value={{ step, nextStep, prevStep, updateData, formData, totalSteps }}
      >
        {children}
      </StepContext.Provider>
    );
  }

  function useStep() {
    const context = useContext(StepContext);
    if (!context) {
      throw new Error("useStep deve ser usado dentro de StepProvider");
    }
    return context;
  }

  return { StepProvider, useStep };
}

export { createStepContext };