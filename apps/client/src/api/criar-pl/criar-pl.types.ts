export type CriarPLRequest = {
  text: string;
  origem_legislativa?: string;
  referencias?: string;
};

export type CriarPLResponse = {
  full_markdown: string;
};