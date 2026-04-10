import { Control } from "react-hook-form";
import { CardSelectableSchemaType } from "./card-selectable.schema";

export interface CardSelectableProps {
  id: string;
  title: string;
  description: string;
  footer: string;
  control: Control<CardSelectableSchemaType>;
  chunkDescription: string;
  author: string;
  detail: React.ReactNode;
}
