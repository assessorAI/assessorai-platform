export type DocViewerProps = {
  title: string;
  content: string;
  isLoading?: boolean;
  color?: DocViewerColor;
};

export enum DocViewerColor {
  ACCENT = "accent",
  SECONDARY = "secondary",
}