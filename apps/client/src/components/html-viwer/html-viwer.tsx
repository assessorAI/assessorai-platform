type Props = {
  html: string;
};

export function HtmlViewer({ html }: Props) {
  return (
    <div
      className="prose prose-gray max-w-none"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
