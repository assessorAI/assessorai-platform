import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DocViewer } from "./doc-viewer";

// Mocks
jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn() },
}));

jest.mock("../html-viwer/html-viwer", () => ({
  HtmlViewer: ({ html }: { html: string }) => (
    <div data-testid="html-viewer" dangerouslySetInnerHTML={{ __html: html }} />
  ),
}));

jest.mock("../card-loading/card-loading", () => ({
  CardLoading: () => <div data-testid="card-loading">Loading...</div>,
}));

const markdownToSafeHtml = jest.fn((md: string) => `<p>${md}</p>`);
jest.mock("@/lib/markdown/markdown.client", () => ({
  markdownToSafeHtml: (md: string) => markdownToSafeHtml(md),
}));

beforeEach(() => {
  jest.clearAllMocks();

  // Mock Clipboard API
  // @ts-expect-error - jsdom doesn't have clipboard by default
  global.navigator.clipboard = {
    write: jest.fn().mockResolvedValue(undefined),
  };

  // @ts-expect-error - define ClipboardItem for tests
  global.ClipboardItem = function ClipboardItem(this: unknown, data: unknown) {
    // @ts-expect-error - ClipboardItem is not defined in jsdom
    this.data = data;
  };
});

describe("DocViewer", () => {
  test("deve copiar texto para a area de transferencia", async () => {
    render(
      <DocViewer
        title="PL"
        content="# Título\nTexto"
        isLoading={false}
      />
    );

    await waitFor(() => expect(markdownToSafeHtml).toHaveBeenCalled());

    await userEvent.click(
      screen.getByRole("button", { name: /copiar texto/i })
    );

    expect(navigator.clipboard.write).toHaveBeenCalledTimes(1);
    expect(navigator.clipboard.write).toHaveBeenCalledWith(expect.any(Array));
  });

  test("deve converter markdown em html", async () => {
    render(
      <DocViewer
        title="PL"
        content="**negrito**"
        isLoading={false}
      />
    );

    await waitFor(() =>
      expect(markdownToSafeHtml).toHaveBeenCalledWith("**negrito**")
    );

    const htmlViewer = await screen.findByTestId("html-viewer");
    expect(htmlViewer.innerHTML).toBe("<p>**negrito**</p>");
  });

  test("deve aparecer o CardLoading e desaparecer o HtmlViewer quando isLoading é true", () => {
    render(
      <DocViewer
        title="PL"
        content="conteudo"
        isLoading={true}
      />
    );

    expect(screen.getByTestId("card-loading")).toBeInTheDocument();
    expect(screen.queryByTestId("html-viewer")).not.toBeInTheDocument();
  });

  test("deve desaparecer o CardLoading e aparecer o HtmlViewer quando isLoading mudar para false", async () => {
    const { rerender } = render(
      <DocViewer
        title="PL"
        content="conteudo"
        isLoading={true}  
      />
    );

    rerender(
      <DocViewer
        title="PL"
        content="conteudo"
        isLoading={false}
      />
    );

    expect(screen.queryByTestId("card-loading")).not.toBeInTheDocument();
    expect(await screen.findByTestId("html-viewer")).toBeInTheDocument();
  });
});
