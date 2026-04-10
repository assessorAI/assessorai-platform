import { renderHook, waitFor } from "@testing-library/react";
import { useSession, signOut } from "next-auth/react";
import { toast } from "sonner";
import { useSessionMonitor } from "./useSessionMonitor";

// Mock do next-auth/react
jest.mock("next-auth/react");

// Mock do sonner
jest.mock("sonner", () => ({
  toast: {
    warning: jest.fn(),
    error: jest.fn(),
  },
}));

// Type helpers para os mocks
const mockedUseSession = useSession as jest.MockedFunction<typeof useSession>;
const mockedSignOut = signOut as jest.MockedFunction<typeof signOut>;
const mockedToast = toast as jest.Mocked<typeof toast>;

describe("useSessionMonitor", () => {
  // Constantes do hook
  const CLOCK_TOLERANCE_MS = 2 * 60 * 1000; // 2 minutos
  const TIME_TO_REDIRECT = 2000; // 2 segundos

  beforeEach(() => {
    // Limpa todos os mocks antes de cada teste
    jest.clearAllMocks();
    jest.clearAllTimers();
    // Usa fake timers para controlar o tempo nos testes
    jest.useFakeTimers();
  });

  afterEach(() => {
    // Restaura os timers reais após cada teste
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe("Sessão válida - ainda tem muito tempo", () => {
    test("não deve mostrar avisos quando a sessão expira em mais de 5 minutos", () => {
      // Arrange: Sessão que expira daqui a 10 minutos
      const now = new Date();
      const expiresAt = new Date(now.getTime() + 10 * 60 * 1000);

      mockedUseSession.mockReturnValue({
        data: {
          user: { name: "Test User" },
          expiresAt: expiresAt.toISOString(),
        },
        status: "authenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act: Renderiza o hook
      renderHook(() => useSessionMonitor());

      // Assert: Não deve mostrar avisos
      expect(mockedToast.warning).not.toHaveBeenCalled();
      expect(mockedToast.error).not.toHaveBeenCalled();
      expect(mockedSignOut).not.toHaveBeenCalled();
    });

    test("não deve mostrar avisos quando a sessão expira em mais de 5 minutos (após tolerância)", () => {
      // Arrange: Sessão que expira daqui a 6 minutos no servidor
      // timeLeft = 6min - 2min(tolerância) = 4 minutos (acima de WARNING_MINUTES)
      const now = new Date();
      const expiresAt = new Date(now.getTime() + 6 * 60 * 1000);

      mockedUseSession.mockReturnValue({
        data: {
          user: { name: "Test User" },
          expiresAt: expiresAt.toISOString(),
        },
        status: "authenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act
      renderHook(() => useSessionMonitor());

      // Assert
      expect(mockedToast.warning).not.toHaveBeenCalled();
      expect(mockedToast.error).not.toHaveBeenCalled();
    });
  });

  describe("Aviso de expiração - 3 minutos antes", () => {
    test("deve mostrar aviso quando faltam exatamente 3 minutos para expirar", () => {
      // Arrange: Sessão que expira daqui a 3 minutos (após aplicar tolerância)
      const now = new Date();
      // timeLeft = expiresAt - now - CLOCK_TOLERANCE_MS
      // Para timeLeft ser 3 minutos, precisamos:
      // expiresAt - now = 3 minutos + 2 minutos (tolerância) = 5 minutos
      const expiresAt = new Date(now.getTime() + 5 * 60 * 1000);

      mockedUseSession.mockReturnValue({
        data: {
          user: { name: "Test User" },
          expiresAt: expiresAt.toISOString(),
        },
        status: "authenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act
      renderHook(() => useSessionMonitor());

      // Assert: Deve mostrar aviso
      expect(mockedToast.warning).toHaveBeenCalledWith(
        "Sessão expirando em breve",
        {
          description: "Sua sessão expirará em 3 minutos. Você será redirecionado para o login.",
          duration: 3000,
        }
      );
      expect(mockedSignOut).not.toHaveBeenCalled();
    });

    test("deve mostrar aviso quando faltam 2 minutos para expirar", () => {
      // Arrange: timeLeft = 2 minutos
      const now = new Date();
      // timeLeft = expiresAt - now - 2min(tolerância) = 2min
      // expiresAt - now = 4min
      const expiresAt = new Date(now.getTime() + 4 * 60 * 1000);

      mockedUseSession.mockReturnValue({
        data: {
          user: { name: "Test User" },
          expiresAt: expiresAt.toISOString(),
        },
        status: "authenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act
      renderHook(() => useSessionMonitor());

      // Assert
      expect(mockedToast.warning).toHaveBeenCalledWith(
        "Sessão expirando em breve",
        {
          description: "Sua sessão expirará em 2 minutos. Você será redirecionado para o login.",
          duration: 3000,
        }
      );
    });

    test("deve mostrar aviso quando falta 1 minuto para expirar", () => {
      // Arrange: timeLeft = 1 minuto
      const now = new Date();
      // timeLeft = expiresAt - now - 2min(tolerância) = 1min
      // expiresAt - now = 3min
      const expiresAt = new Date(now.getTime() + 3 * 60 * 1000);

      mockedUseSession.mockReturnValue({
        data: {
          user: { name: "Test User" },
          expiresAt: expiresAt.toISOString(),
        },
        status: "authenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act
      renderHook(() => useSessionMonitor());

      // Assert
      expect(mockedToast.warning).toHaveBeenCalledWith(
        "Sessão expirando em breve",
        {
          description: "Sua sessão expirará em 1 minutos. Você será redirecionado para o login.",
          duration: 3000,
        }
      );
    });

    test("não deve mostrar aviso duplicado se o hook renderizar novamente", () => {
      // Arrange: timeLeft = 3 minutos (para mostrar aviso)
      const now = new Date();
      const expiresAt = new Date(now.getTime() + 5 * 60 * 1000);

      mockedUseSession.mockReturnValue({
        data: {
          user: { name: "Test User" },
          expiresAt: expiresAt.toISOString(),
        },
        status: "authenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act: Renderiza o hook e depois re-renderiza
      const { rerender } = renderHook(() => useSessionMonitor());
      
      expect(mockedToast.warning).toHaveBeenCalledTimes(1);
      
      // Re-renderiza o hook
      rerender();

      // Assert: Deve continuar com apenas 1 chamada (não duplica)
      expect(mockedToast.warning).toHaveBeenCalledTimes(1);
    });
  });

  describe("Sessão expirada - logout automático", () => {
    test("deve fazer logout quando a sessão expira (timeLeft <= 0)", async () => {
      // Arrange: Sessão expirada (considerando tolerância)
      const now = new Date();
      // timeLeft = expiresAt - now + 2min <= 0
      // expiresAt - now <= -2min
      const expiresAt = new Date(now.getTime() - 3 * 60 * 1000);

      mockedUseSession.mockReturnValue({
        data: {
          user: { name: "Test User" },
          expiresAt: expiresAt.toISOString(),
        },
        status: "authenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act
      renderHook(() => useSessionMonitor());

      // Assert: Deve mostrar toast de erro
      expect(mockedToast.error).toHaveBeenCalledWith("Sessão expirada", {
        description:
          "Sua sessão expirou. Você será redirecionado para o login em alguns instantes.",
        duration: 5000,
      });

      // Avança o tempo para o timeout do redirect (2 segundos)
      jest.advanceTimersByTime(TIME_TO_REDIRECT);

      // Assert: Deve chamar signOut
      await waitFor(() => {
        expect(mockedSignOut).toHaveBeenCalledWith({ callbackUrl: "/login" });
      });
    });

    test("deve fazer logout exatamente no momento da expiração (timeLeft = 0)", async () => {
      // Arrange: timeLeft = 0
      const now = new Date();
      // expiresAt - now + 2min = 0
      // expiresAt - now = -2min
      const expiresAt = new Date(now.getTime() - CLOCK_TOLERANCE_MS);

      mockedUseSession.mockReturnValue({
        data: {
          user: { name: "Test User" },
          expiresAt: expiresAt.toISOString(),
        },
        status: "authenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act
      renderHook(() => useSessionMonitor());

      // Assert: Deve mostrar toast
      expect(mockedToast.error).toHaveBeenCalled();

      // Avança para o redirect
      jest.advanceTimersByTime(TIME_TO_REDIRECT);

      await waitFor(() => {
        expect(mockedSignOut).toHaveBeenCalled();
      });
    });

    test("não deve fazer logout duplicado se hook renderizar novamente", async () => {
      // Arrange: Sessão expirada
      const now = new Date();
      const expiresAt = new Date(now.getTime() - 3 * 60 * 1000);

      mockedUseSession.mockReturnValue({
        data: {
          user: { name: "Test User" },
          expiresAt: expiresAt.toISOString(),
        },
        status: "authenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act
      const { rerender } = renderHook(() => useSessionMonitor());

      expect(mockedToast.error).toHaveBeenCalledTimes(1);

      // Re-renderiza
      rerender();

      // Assert: Não deve chamar novamente
      expect(mockedToast.error).toHaveBeenCalledTimes(1);

      // Avança o tempo
      jest.advanceTimersByTime(TIME_TO_REDIRECT);

      await waitFor(() => {
        expect(mockedSignOut).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe("Verificação periódica - intervalo de 30 segundos", () => {
    test("deve verificar a expiração a cada 30 segundos", () => {
      // Arrange: Sessão válida por 10 minutos
      const now = new Date();
      const expiresAt = new Date(now.getTime() + 10 * 60 * 1000);

      mockedUseSession.mockReturnValue({
        data: {
          user: { name: "Test User" },
          expiresAt: expiresAt.toISOString(),
        },
        status: "authenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act
      renderHook(() => useSessionMonitor());

      // Assert: Não mostra aviso inicialmente
      expect(mockedToast.warning).not.toHaveBeenCalled();

      // Avança 30 segundos
      jest.advanceTimersByTime(30000);

      // Ainda não deve mostrar aviso (ainda tem tempo)
      expect(mockedToast.warning).not.toHaveBeenCalled();

      // Avança mais 30 segundos (total 60 segundos)
      jest.advanceTimersByTime(30000);

      // Continua sem avisos
      expect(mockedToast.warning).not.toHaveBeenCalled();
    });

    test("deve detectar expiração durante verificação periódica", async () => {
      // Arrange: Sessão que muda de válida para expirando
      let callCount = 0;
      const initialTime = new Date();
      
      mockedUseSession.mockImplementation(() => {
        callCount++;
        // Na primeira chamada, sessão válida (timeLeft = 6 minutos após tolerância)
        // Nas próximas, sessão expirando (timeLeft = 3 minutos após tolerância)
        const expiresAt = callCount === 1
          ? new Date(initialTime.getTime() + 8 * 60 * 1000)  // 8min - 2min = 6min
          : new Date(initialTime.getTime() + 5 * 60 * 1000); // 5min - 2min = 3min

        return {
          data: {
            user: { name: "Test User" },
            expiresAt: expiresAt.toISOString(),
          },
          status: "authenticated",
          update: jest.fn(),
        } as unknown as ReturnType<typeof useSession>;
      });

      // Act
      const { rerender } = renderHook(() => useSessionMonitor());

      // Inicialmente sem avisos (timeLeft = 6 minutos)
      expect(mockedToast.warning).not.toHaveBeenCalled();

      // Simula mudança de dados da sessão
      rerender();

      // Avança 30 segundos para o próximo check
      jest.advanceTimersByTime(30000);

      // Assert: Deve detectar que está expirando (timeLeft = 3 minutos)
      expect(mockedToast.warning).toHaveBeenCalled();
    });

    test("deve parar o intervalo quando a sessão expira", async () => {
      // Arrange: Sessão já expirada                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
      const now = new Date();
      const expiresAt = new Date(now.getTime() - 3 * 60 * 1000);

      mockedUseSession.mockReturnValue({
        data: {
          user: { name: "Test User" },
          expiresAt: expiresAt.toISOString(),
        },
        status: "authenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act
      renderHook(() => useSessionMonitor());

      // Toast de erro deve ser chamado imediatamente
      expect(mockedToast.error).toHaveBeenCalledTimes(1);

      // Avança 30 segundos (tempo do intervalo)
      jest.advanceTimersByTime(30000);

      // Assert: Não deve chamar novamente (intervalo foi parado)
      expect(mockedToast.error).toHaveBeenCalledTimes(1);

      // Avança mais 30 segundos
      jest.advanceTimersByTime(30000);

      // Continua com apenas 1 chamada
      expect(mockedToast.error).toHaveBeenCalledTimes(1);
    });
  });

  describe("Limpeza de recursos - unmount", () => {
    test("deve limpar o intervalo quando o componente desmonta", () => {
      // Arrange
      const now = new Date();
      const expiresAt = new Date(now.getTime() + 10 * 60 * 1000);

      mockedUseSession.mockReturnValue({
        data: {
          user: { name: "Test User" },
          expiresAt: expiresAt.toISOString(),
        },
        status: "authenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act
      const { unmount } = renderHook(() => useSessionMonitor());

      // Desmonta o hook
      unmount();

      // Avança o tempo
      jest.advanceTimersByTime(30000);

      // Assert: Não deve ter chamado nada (intervalo foi limpo)
      expect(mockedToast.warning).not.toHaveBeenCalled();
      expect(mockedToast.error).not.toHaveBeenCalled();
    });
  });

  describe("Casos edge - sessão null ou undefined", () => {
    test("não deve crashar quando session é null", () => {
      // Arrange
      mockedUseSession.mockReturnValue({
        data: null,
        status: "unauthenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act & Assert: Não deve crashar
      expect(() => {
        renderHook(() => useSessionMonitor());
      }).not.toThrow();

      expect(mockedToast.warning).not.toHaveBeenCalled();
      expect(mockedToast.error).not.toHaveBeenCalled();
    });

    test("não deve crashar quando expiresAt não existe", () => {
      // Arrange
      mockedUseSession.mockReturnValue({
        data: {
          user: { name: "Test User" },
          // expiresAt não definido
        },
        status: "authenticated",
        update: jest.fn(),
      } as unknown as ReturnType<typeof useSession>);

      // Act & Assert: Não deve crashar
      expect(() => {
        renderHook(() => useSessionMonitor());
      }).not.toThrow();
    });
  });
});
