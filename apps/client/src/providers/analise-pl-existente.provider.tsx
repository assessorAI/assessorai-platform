import { createContext, useContext, useState } from "react";

// Interface
interface AnalisePlExistenteContextType {
  isLoading: boolean;
  setIsLoading: (isLoading: boolean) => void;
}

// Context
const AnalisePlExistenteContext = createContext<AnalisePlExistenteContextType | undefined>(undefined);

// Provider
export const AnalisePlExistenteProvider = ({ children }: { children: React.ReactNode }) => {
  const [isLoading, setIsLoading] = useState<boolean>(false);

  return (
    <AnalisePlExistenteContext.Provider value={{ isLoading, setIsLoading }
    }>
      {children}
    </AnalisePlExistenteContext.Provider>
  );
};

// Hook
export const useAnalisePlExistente = () => {
  const context = useContext(AnalisePlExistenteContext);
  if (!context) {
    throw new Error('useAnalisePlExistente must be used within an AnalisePlExistenteProvider');
  }
  return context;
};