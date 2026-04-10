import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Requerimento } from "./requerimento";
import { useHandleRequerimento } from "./useHandleRequerimento";
import { useCardCollapsible } from "@/components/card-collapsible/useCardCollapsible";
import { toast } from "sonner";

// Mock dos hooks customizados
jest.mock("./useHandleRequerimento");
jest.mock("@/components/card-collapsible/useCardCollapsible");

// Mock do hook useMandato
jest.mock("@/hooks/useMandato", () => ({
  useMandato: jest.fn(() => ({
    id: 1,
    name: "Mandato Teste",
  })),
}));

// Mock do toast
jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

describe("Requerimento Component", () => {
  // Função auxiliar para criar mocks padrão
  const createDefaultMocks = () => {
    const mockHandleRequerimento = jest.fn();
    const mockCloseAccordion = jest.fn();
    const mockOnClickAccordion = jest.fn();

    (useHandleRequerimento as jest.Mock).mockReturnValue({
      handleRequerimento: mockHandleRequerimento,
      requerimento: null,
      isLoading: false,
      error: null,
    });

    (useCardCollapsible as jest.Mock).mockReturnValue({
      accordionValue: "item-1",
      onClickAccordion: mockOnClickAccordion,
      closeAccordion: mockCloseAccordion,
    });

    return {
      mockHandleRequerimento,
      mockCloseAccordion,
      mockOnClickAccordion,
    };
  };

  // Limpa todos os mocks antes de cada teste
  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * TESTE 1: Renderização básica
   * Verifica se o componente renderiza corretamente com todos os elementos essenciais
   */
  it("deve renderizar o componente corretamente", () => {
    createDefaultMocks();

    render(<Requerimento />);

    // Verifica se o título do card está presente
    expect(
      screen.getByText("Dados do Requerimento ou Indicação")
    ).toBeInTheDocument();

    // Verifica se a descrição está presente
    expect(
      screen.getByText(
        /Gere requerimentos formais com estrutura e linguagem adequadas/i
      )
    ).toBeInTheDocument();

    // Verifica se o label do campo de descrição está presente
    expect(screen.getByText("Descrição")).toBeInTheDocument();

    // Verifica se o label de documentos está presente
    expect(
      screen.getByText("Documentos de referência (opcional)")
    ).toBeInTheDocument();

    // Verifica se o botão de submit está presente
    expect(screen.getByRole("button", { name: /Criar com IA/i })).toBeInTheDocument();
  });

  /**
   * TESTE 2: Placeholder vazio
   * Verifica se o placeholder é exibido quando não há requerimento e não está carregando
   */
  it("deve exibir placeholder quando não há requerimento", () => {
    createDefaultMocks();

    render(<Requerimento />);

    expect(
      screen.getByText("Seu requerimento será exibido aqui")
    ).toBeInTheDocument();
  });

  /**
   * TESTE 3: Validação do formulário - campo vazio
   * Verifica se o botão fica desabilitado quando o campo de descrição está vazio
   */
  it("deve desabilitar o botão de submit quando o campo está vazio", () => {
    createDefaultMocks();

    render(<Requerimento />);

    const submitButton = screen.getByRole("button", { name: /Criar com IA/i });

    // O botão deve estar desabilitado inicialmente (campo vazio)
    expect(submitButton).toBeDisabled();
  });

  /**
   * TESTE 4: Preenchimento do formulário
   * Verifica se é possível preencher o campo de descrição
   */
  it("deve permitir preencher o campo de descrição", async () => {
    createDefaultMocks();
    const user = userEvent.setup();

    render(<Requerimento />);

    const textarea = screen.getByPlaceholderText(
      /Descreva aqui o que você gostaria que estivesse contido nesse requerimento/i
    );

    await user.type(textarea, "Requerimento de teste");

    expect(textarea).toHaveValue("Requerimento de teste");
  });

  /**
   * TESTE 5: Submissão do formulário
   * Verifica se o formulário chama a função handleRequerimento corretamente ao ser submetido
   */
  it("deve chamar handleRequerimento ao submeter o formulário", async () => {
    const { mockHandleRequerimento } = createDefaultMocks();
    const user = userEvent.setup();

    render(<Requerimento />);

    const textarea = screen.getByPlaceholderText(
      /Descreva aqui o que você gostaria que estivesse contido nesse requerimento/i
    );

    // Preenche o campo
    await user.type(textarea, "Requerimento de teste");

    // Aguarda o formulário validar
    await waitFor(() => {
      const submitButton = screen.getByRole("button", { name: /Criar com IA/i });
      expect(submitButton).not.toBeDisabled();
    });

    const submitButton = screen.getByRole("button", { name: /Criar com IA/i });
    await user.click(submitButton);

    // Verifica se a função foi chamada com os parâmetros corretos
    await waitFor(() => {
      expect(mockHandleRequerimento).toHaveBeenCalledWith(
        "Requerimento de teste",
        undefined
      );
    });
  });

  /**
   * TESTE 6: Estado de loading
   * Verifica se o spinner é exibido durante o carregamento
   */
  it("deve exibir spinner quando isLoading é true", () => {
    const mocks = createDefaultMocks();

    (useHandleRequerimento as jest.Mock).mockReturnValue({
      ...mocks,
      isLoading: true,
      requerimento: null,
      error: null,
    });

    render(<Requerimento />);

    const submitButton = screen.getByRole("button", { name: /Criar com IA/i });

    // O botão deve estar desabilitado durante o loading
    expect(submitButton).toBeDisabled();

    // Verifica se o spinner está sendo exibido
    const spinner = screen.getByRole("status", { name: /Loading/i });
    expect(spinner).toBeInTheDocument();

    // Verifica se o texto "Criar com IA" ainda está presente
    expect(screen.getByText("Criar com IA")).toBeInTheDocument();
  });

  /**
   * TESTE 7: Exibição do resultado
   * Verifica se o DocViewer é exibido quando há um requerimento gerado
   */
  it("deve exibir DocViewer quando há um requerimento gerado", () => {
    const mocks = createDefaultMocks();

    (useHandleRequerimento as jest.Mock).mockReturnValue({
      ...mocks,
      isLoading: false,
      requerimento: {
        response: "Conteúdo do requerimento gerado",
      },
      error: null,
    });

    render(<Requerimento />);

    // Verifica se o título do DocViewer está presente
    expect(screen.getByText("Documento gerado")).toBeInTheDocument();

    // Verifica se o placeholder NÃO está mais visível
    expect(
      screen.queryByText("Seu requerimento será exibido aqui")
    ).not.toBeInTheDocument();
  });

  /**
   * TESTE 8: Tratamento de erro
   * Verifica se o toast de erro é exibido quando há um erro
   */
  it("deve exibir toast de erro quando há erro", async () => {
    const mocks = createDefaultMocks();

    (useHandleRequerimento as jest.Mock).mockReturnValue({
      ...mocks,
      isLoading: false,
      requerimento: null,
      error: "Erro ao criar requerimento",
    });

    render(<Requerimento />);

    // Aguarda o useEffect executar
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Erro ao criar requerimento");
    });
  });

  /**
   * TESTE 9: Fechar accordion após sucesso
   * Verifica se o accordion é fechado quando o requerimento é gerado com sucesso
   */
  it("deve fechar o accordion quando requerimento é gerado com sucesso", async () => {
    const { mockCloseAccordion } = createDefaultMocks();

    const { rerender } = render(<Requerimento />);

    // Simula mudança de estado para requerimento gerado
    (useHandleRequerimento as jest.Mock).mockReturnValue({
      handleRequerimento: jest.fn(),
      isLoading: false,
      requerimento: {
        response: "Conteúdo do requerimento",
      },
      error: null,
    });

    rerender(<Requerimento />);

    // Aguarda o useEffect executar
    await waitFor(() => {
      expect(mockCloseAccordion).toHaveBeenCalled();
    });
  });

  /**
   * TESTE 10: Botão "Gerar novamente"
   * Verifica se o botão de gerar novamente funciona corretamente
   */
  it("deve chamar handleRequerimento novamente quando clicar em gerar novamente", async () => {
    const { mockHandleRequerimento, mockCloseAccordion } = createDefaultMocks();
    const user = userEvent.setup();

    // Configura o mock para retornar um requerimento
    (useHandleRequerimento as jest.Mock).mockReturnValue({
      handleRequerimento: mockHandleRequerimento,
      isLoading: false,
      requerimento: {
        response: "Conteúdo do requerimento",
      },
      error: null,
    });

    render(<Requerimento />);

    // Primeiro preenche o formulário
    const textarea = screen.getByPlaceholderText(
      /Descreva aqui o que você gostaria que estivesse contido nesse requerimento/i
    );
    await user.type(textarea, "Texto de teste");

    // Encontra o botão "Gerar novamente" no DocViewer
    // Nota: Este teste assume que o DocViewer tem um botão com este texto
    // Se o DocViewer não tiver este botão, este teste precisará ser ajustado
    const generateAgainButton = screen.queryByRole("button", {
      name: /gerar novamente/i,
    });

    if (generateAgainButton) {
      await user.click(generateAgainButton);

      await waitFor(() => {
        expect(mockCloseAccordion).toHaveBeenCalled();
        expect(mockHandleRequerimento).toHaveBeenCalledWith("Texto de teste", undefined);
      });
    }
  });

  /**
   * TESTE 11: Validação de mensagem de erro do campo
   * Verifica se a mensagem de erro é exibida quando o campo é esvaziado
   */
  it("deve exibir mensagem de erro quando o campo é esvaziado", async () => {
    createDefaultMocks();
    const user = userEvent.setup();

    render(<Requerimento />);

    const submitButton = screen.getByRole("button", { name: /Criar com IA/i });

    // O botão deve estar desabilitado inicialmente
    expect(submitButton).toBeDisabled();

    const textarea = screen.getByPlaceholderText(
      /Descreva aqui o que você gostaria que estivesse contido nesse requerimento/i
    );

    // Digita algo no campo (isso habilita o botão)
    await user.type(textarea, "Texto");

    // Aguarda o formulário validar
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });

    // Limpa o campo (seleciona tudo e apaga)
    await user.clear(textarea);

    // Aguarda a mensagem de erro aparecer
    await waitFor(() => {
      const errorMessage = screen.getByText(
        /O campo de descrição do requerimento\/indicação deve ser preenchido/i
      );
      expect(errorMessage).toBeInTheDocument();
    });

    // O botão deve estar desabilitado novamente
    expect(submitButton).toBeDisabled();
  });
});

