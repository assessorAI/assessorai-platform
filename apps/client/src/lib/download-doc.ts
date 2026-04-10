"use client";

/**
 * Converte HTML em um arquivo .docx (Word OOXML) e faz o download.
 */
export async function downloadHtmlAsDoc(html: string, filename = "document.docx") {
  const response = await fetch("/api/convert-html-to-docx", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ html, filename }),
  });

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}