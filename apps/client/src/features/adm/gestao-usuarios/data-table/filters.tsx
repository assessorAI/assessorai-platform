import { cargo } from "@/types/user.types";
import { PermissionLevel } from "@/types/user.types";
import { Button } from "@/components/ui/button";
import { MultiSelect } from "@/components/multiselect/multiselect";
import { DatePickerRange } from "@/components/ui/datepicker-range";
import { DateRange } from "react-day-picker";


interface FiltersProps {
  role: string[];
  permission_level: string[];
  dateRange: DateRange | undefined;
  onDateRangeChange: (dateRange: DateRange | undefined) => void;
  onRoleChange: (role: string[]) => void;
  onPermissionChange: (permission: string[]) => void;
}

export function Filters({
  role,
  permission_level,
  dateRange,
  onDateRangeChange,
  onRoleChange,
  onPermissionChange
}: FiltersProps) {
  const hasFilters = role.length > 0 || permission_level.length > 0 || dateRange;

  const cargoOptions = cargo.map((cargoItem) => ({
    value: cargoItem,
    label: cargoItem,
  }));

  const acessoOptions = [
    { value: PermissionLevel.Admin, label: "Administrador" },
    { value: PermissionLevel.Manager, label: "Gerente do mandato" },
    { value: PermissionLevel.User, label: "Membro do mandato" },
    { value: PermissionLevel.Viewer, label: "Visualizador" },
  ];

  return (
    <div className="grid grid-cols-[1fr_auto] gap-4 items-start">
      <div className="flex gap-2 flex-wrap">
        <div className="min-w-[200px]">
          <MultiSelect
            options={cargoOptions}
            onValueChange={onRoleChange}
            defaultValue={role}
            placeholder="Cargo"
            maxCount={2}
          />
        </div>
        <div className="min-w-[200px]">
          <MultiSelect
            options={acessoOptions}
            onValueChange={onPermissionChange}
            defaultValue={permission_level}
            placeholder="Acesso"
            maxCount={2}
          />
        </div>

        <div className="min-w-[200px]">
          <DatePickerRange
            placeholder="Período de acesso"
            value={dateRange}
            onChange={onDateRangeChange}
          />
        </div>
      </div>
      {hasFilters && (
        <div className="min-w-[200px]">
          <Button variant="link" onClick={() => {
            onRoleChange([]);
            onPermissionChange([]);
            onDateRangeChange(undefined);
          }}>
            Limpar filtros
          </Button>
        </div>
      )}

    </div>
  );
}