import { Column, Table } from "@tanstack/react-table";
import { Button } from "../ui/button";
import { ArrowUpDown } from "lucide-react";

type SortableButtonProps = {
  column: Column<unknown>;
  children: React.ReactNode;
  columnId: string;
  currentOrderBy?: string;
  onOrderByChange?: (orderBy: string) => void;
};

export const SortableButton = ({
    children,
    columnId,
    currentOrderBy = "",
    onOrderByChange,
  }: SortableButtonProps) => {

    const handleClick = () => {
      let nextOrderBy = "";

      if (currentOrderBy === columnId) {
        // Crescente → Decrescente
        nextOrderBy = `-${columnId}`;
      } else if (currentOrderBy === `-${columnId}`) {
        // Decrescente → Sem ordenação
        nextOrderBy = "";
      } else {
        // Sem ordenação → Crescente
        nextOrderBy = columnId;
      }

      onOrderByChange?.(nextOrderBy);
    };

    return (
      <Button
        variant="ghost"
        className="text-muted-foreground font-medium !p-0 hover:bg-transparent"
        onClick={handleClick}
      >
        {children}
        <ArrowUpDown className="size-4 " />
      </Button>
    );
  };

export const headerWithOrderBy = <TData,>(column: Column<TData, unknown>, table: Table<TData>) => {
    const { orderBy, onOrderByChange } = table.options.meta as {
      orderBy?: string;
      onOrderByChange?: (orderBy: string) => void;
    };
    const columnId = column.id;
    return (
      <SortableButton 
        column={column as Column<unknown>} 
        columnId={columnId} 
        currentOrderBy={orderBy} 
        onOrderByChange={onOrderByChange}
      >
        {(column.columnDef.meta as { label?: string })?.label ?? column.id}
      </SortableButton>
    );
  }