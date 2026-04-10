"use client";
import { createContext, useState, useContext } from "react";

export interface ProjetoReferencia {
  id: string;
  title: string;
  author: string;
  house: string;
  subject: string;
  chunk_text: string;
  url: string;
}

type ProjetosReferenciasContextType = {
  selectedProjetos: ProjetoReferencia[];
  setSelectedProjetos: (projetos: ProjetoReferencia[]) => void;
  clearSelectedProjetos: () => void;
};

const ProjetosContext = createContext<
  ProjetosReferenciasContextType | undefined
>(undefined);

export function ProjetosReferenciaProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [selectedProjetos, setSelectedProjetos] = useState<ProjetoReferencia[]>(
    []
  );

  const clearSelectedProjetos = () => {
    setSelectedProjetos([]);
  }

  return (
    <ProjetosContext.Provider value={{ selectedProjetos, setSelectedProjetos, clearSelectedProjetos }}>
      {children}
    </ProjetosContext.Provider>
  );
}

export function useProjetosReferencias() {
  const context = useContext(ProjetosContext);
  if (!context) {
    throw new Error(
      "useProjetosReferencias must be used within a ProjetosReferenciaProvider"
    );
  }
  return context;
}
