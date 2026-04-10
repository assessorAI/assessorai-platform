import { marked } from "marked";
import createDOMPurify from "dompurify";

export function markdownToSafeHtml(markdown: string) {
  const dirty = marked.parse(markdown, { async: false }) as string;
  const DOMPurify = createDOMPurify(window);
  return DOMPurify.sanitize(dirty);
}
