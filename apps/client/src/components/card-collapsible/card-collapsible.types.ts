export interface CardCollapsibleProps {
  title: string;
  description: string;
  tooltip?: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  value?: string | undefined;
  onValueChange?: (value: string | undefined) => void;
  content: React.ReactNode;
  color?: CardCollapsibleColor;
}

export enum CardCollapsibleColor {
  ACCENT = "accent",
  SECONDARY = "secondary",
}