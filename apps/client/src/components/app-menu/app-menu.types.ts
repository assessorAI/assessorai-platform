export interface MenuItem {
  title: string;
  url?: string;
  icon: React.ElementType;
  items?: { title: string; url: string }[];
}