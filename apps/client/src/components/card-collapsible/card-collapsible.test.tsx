import React, { createContext, useContext } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CardCollapsible } from "./card-collapsible";

jest.mock("./card-collapsible.scss", () => ({}));

// Mock Accordion com contexto simples para controlar valor do item atual
jest.mock("../ui/accordion", () => {
  const AccordionCtx = createContext<{
    value: string | undefined;
    onValueChange: (v: string | undefined) => void;
  }>({
    value: undefined,
    onValueChange: () => {},
  });
  const ItemCtx = createContext<string | undefined>(undefined);

  function Accordion({
    value,
    onValueChange,
    children,
  }: {
    value?: string;
    onValueChange: (v: string | undefined) => void;
    children: React.ReactNode;
  }) {
    return (
      <AccordionCtx.Provider value={{ value, onValueChange }}>
        <div data-testid="accordion">{children}</div>
      </AccordionCtx.Provider>
    );
  }

  function AccordionItem({
    value,
    children,
  }: {
    value: string;
    children: React.ReactNode;
  }) {
    return (
      <ItemCtx.Provider value={value}>
        <div data-testid={`accordion-item-${value}`}>{children}</div>
      </ItemCtx.Provider>
    );
  }

  function AccordionTrigger({
    children,
    ...rest
  }: React.HTMLAttributes<HTMLButtonElement>) {
    const { value, onValueChange } = useContext(AccordionCtx);
    const itemValue = useContext(ItemCtx);
    return (
      <button
        aria-label="accordion-trigger"
        onClick={() =>
          onValueChange(value === itemValue ? undefined : itemValue)
        }
        {...rest}
      >
        {children}
      </button>
    );
  }

  function AccordionContent({ children }: { children: React.ReactNode }) {
    const { value } = useContext(AccordionCtx);
    const itemValue = useContext(ItemCtx);
    if (value !== itemValue) return null;
    return <div data-testid="accordion-content">{children}</div>;
  }

  return { Accordion, AccordionItem, AccordionTrigger, AccordionContent };
});

// Mock Tooltip para expor o conteúdo sempre
jest.mock("../ui/tooltip", () => ({
  TooltipProvider: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
  Tooltip: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  TooltipTrigger: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  TooltipContent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="tooltip-content">{children}</div>
  ),
}));

describe("CardCollapsible", () => {
  const defaultProps = {
    title: "Meu Título",
    description: "Minha descrição",
    icon: <span data-testid="icon">i</span>,
    tooltip: "Dica aqui",
    content: <div data-testid="inner-content">conteúdo interno</div>,
  };

  test("abre por padrão quando defaultOpen = true (não controlado)", async () => {
    render(<CardCollapsible {...defaultProps} defaultOpen />);

    expect(screen.getByTestId("accordion-content")).toBeInTheDocument();
    expect(screen.getByTestId("inner-content")).toBeInTheDocument();
  });

  test("toggle de abrir/fechar no modo não-controlado via trigger", async () => {
    render(<CardCollapsible {...defaultProps} defaultOpen />);

    const trigger = screen.getByLabelText("accordion-trigger");
    // Fecha
    await userEvent.click(trigger);
    expect(screen.queryByTestId("accordion-content")).not.toBeInTheDocument();

    // Reabre
    await userEvent.click(trigger);
    expect(screen.getByTestId("accordion-content")).toBeInTheDocument();
  });

  test("modo controlado: respeita value e chama onValueChange ao clicar", async () => {
    const onValueChange = jest.fn();
    const { rerender } = render(
      <CardCollapsible
        {...defaultProps}
        value={"item-1"}
        onValueChange={onValueChange}
      />
    );

    // Visível porque value = "item-1"
    expect(screen.getByTestId("accordion-content")).toBeInTheDocument();

    // Clicar deve solicitar colapso (undefined)
    await userEvent.click(screen.getByLabelText("accordion-trigger"));
    expect(onValueChange).toHaveBeenCalledWith(undefined);

    // Enquanto o pai não muda "value", continua visível
    expect(screen.getByTestId("accordion-content")).toBeInTheDocument();

    // Simula o pai colapsando
    rerender(
      <CardCollapsible
        {...defaultProps}
        value={undefined}
        onValueChange={onValueChange}
      />
    );
    expect(screen.queryByTestId("accordion-content")).not.toBeInTheDocument();
  });

  test("renderiza título, descrição, ícone e tooltip", () => {
    render(<CardCollapsible {...defaultProps} defaultOpen />);

    expect(screen.getByText("Meu Título")).toBeInTheDocument();
    expect(screen.getByText("Minha descrição")).toBeInTheDocument();
    expect(screen.getByTestId("icon")).toBeInTheDocument();
    expect(screen.getByTestId("tooltip-content")).toHaveTextContent(
      "Dica aqui"
    );
  });
});
