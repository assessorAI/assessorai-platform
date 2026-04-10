import { marked } from "marked";
import createDOMPurify from "dompurify";
import { JSDOM } from "jsdom";

export function markdownToSafeHtml(markdown: string) {
  const dirty = marked.parse(markdown, { async: false }) as string;
  const jsdomWindow = new JSDOM("").window as unknown as Window;
  const DOMPurify = createDOMPurify(jsdomWindow as unknown as typeof globalThis);

  return DOMPurify.sanitize(dirty);
}