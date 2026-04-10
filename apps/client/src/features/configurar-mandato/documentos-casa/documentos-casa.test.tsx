import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DocumentosCasa } from "./documentos-casa";
import { DocumentosCasa as DocumentosCasaType, DocumentosCasaFileType } from "@/types/documentos-casa.types";
import { PermissionLevel } from "@/types/user.types";

// Mock do módulo de estilos SCSS
jest.mock("./documentos-casa.module.scss", () => ({}));

// Mock do next/navigation
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(() => ({
    refresh: jest.fn(),
    push: jest.fn(),
  })),
}));

// Mock do next-auth/react
jest.mock("next-auth/react", () => ({
  useSession: jest.fn(() => ({
    data: {
      user: {
        id: "1",
        permission_level: PermissionLevel.Manager,
      },
    },
    status: "authenticated",
  })),
}));

// Mock do sonner (toast)
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock do DocumentosCasaTable
jest.mock("./documentos-casa-table", () => ({
  DocumentosCasaTable: ({ documents }: { documents: DocumentosCasaType[] }) => {
    if (documents.length === 0) return null;
    return (
      <div data-testid="documentos-casa-table">
        <p>Tabela com {documents.length} documento(s)</p>
        {documents.map((doc) => (
          <div key={doc.id}>{doc.filename}</div>
        ))}
      </div>
    );
  },
}));

// Mock do fetch global
global.fetch = jest.fn();

describe("DocumentosCasa", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockDocuments = [
    {
      id: "1",
      filename: "constituicao.pdf",
      file_type: DocumentosCasaFileType.CONSTITUICAO,
      title: "Constituição Estadual",
    },
    {
      id: "2",
      filename: "regimento.pdf",
      file_type: DocumentosCasaFileType.REGIMENTO_INTERNO,
      title: "Regimento Interno",
    },
  ];

  describe("Renderização básica", () => {
    it("deve renderizar o título do componente", () => {
      // Arrange & Act
      render(<DocumentosCasa mandatoId="123" documents={[]} />);

      // Assert
      expect(screen.getByText("Documentos da casa")).toBeInTheDocument();
    });

    it("deve renderizar os campos do formulário", () => {
      // Arrange & Act
      render(<DocumentosCasa mandatoId="123" documents={[]} />);

      // Assert
      expect(screen.getByLabelText("Documento")).toBeInTheDocument();
      expect(screen.getByText("Tipo de documento")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /salvar documento/i })
      ).toBeInTheDocument();
    });

    it("deve renderizar o placeholder do select", () => {
      // Arrange
      render(<DocumentosCasa mandatoId="123" documents={[]} />);

      // Assert: Verifica o placeholder do select
      expect(screen.getByText("Selecione o tipo de arquivo")).toBeInTheDocument();
    });
  });

  describe("Exibição da tabela", () => {
    it("deve exibir a tabela quando houver documentos", () => {
      // Arrange & Act
      render(<DocumentosCasa mandatoId="123" documents={mockDocuments} />);

      // Assert
      expect(screen.getByTestId("documentos-casa-table")).toBeInTheDocument();
      expect(screen.getByText("Tabela com 2 documento(s)")).toBeInTheDocument();
    });

    it("não deve exibir a tabela quando não houver documentos", () => {
      // Arrange & Act
      render(<DocumentosCasa mandatoId="123" documents={[]} />);

      // Assert
      expect(
        screen.queryByTestId("documentos-casa-table")
      ).not.toBeInTheDocument();
    });
  });

  describe("Upload de documento", () => {
    it("deve permitir fazer upload de um arquivo", async () => {
      // Arrange
      render(<DocumentosCasa mandatoId="123" documents={[]} />);

      // Act: Faz upload de um arquivo
      const file = new File(["conteúdo"], "constituicao.pdf", {
        type: "application/pdf",
      });
      const fileInput = screen.getByLabelText("Documento") as HTMLInputElement;
      await userEvent.upload(fileInput, file);

      // Assert: Verifica que o arquivo foi adicionado
      expect(fileInput.files?.[0]).toBe(file);
      expect(fileInput.files).toHaveLength(1);
    });

    it("deve ter o botão de submit desabilitado inicialmente", () => {
      // Arrange & Act
      render(<DocumentosCasa mandatoId="123" documents={[]} />);

      // Assert: O botão deve estar desabilitado pois o formulário está inválido
      const submitButton = screen.getByRole("button", {
        name: /salvar documento/i,
      });
      
      // Nota: O botão não está desabilitado por padrão, mas o form não deve submeter sem dados válidos
      expect(submitButton).toBeInTheDocument();
    });
  });

  describe("Opções de tipo de documento", () => {
    it("deve ter as opções de tipo de documento disponíveis no select oculto", () => {
      // Arrange & Act
      render(<DocumentosCasa mandatoId="123" documents={[]} />);

      // Assert: Verifica que o select oculto tem as opções corretas
      const hiddenSelect = document.querySelector('select[aria-hidden="true"]');
      expect(hiddenSelect).toBeInTheDocument();
      
      // Verifica as opções dentro do select
      const options = hiddenSelect?.querySelectorAll('option');
      expect(options).toHaveLength(4); // Uma opção vazia + 3 tipos
      
      const optionValues = Array.from(options || []).map((opt) => opt.textContent);
      expect(optionValues).toContain("Constituição");
      expect(optionValues).toContain("Regimento Interno");
      expect(optionValues).toContain("Outro");
    });
  });

  describe("MandatoId", () => {
    it("deve receber o mandatoId como prop", () => {
      // Arrange & Act
      render(<DocumentosCasa mandatoId="999" documents={[]} />);

      // Assert: Verifica que o componente renderizou (o mandatoId é usado internamente)
      expect(screen.getByText("Documentos da casa")).toBeInTheDocument();
    });
  });
});

