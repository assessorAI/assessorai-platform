"use client";

import { partidosPoliticosTSE } from "@/types/partidos-politicos.const";
import { POSICIONAMENTO_MANDATO } from "@/types/mandato.types";
import { PERFIS_MANDATO, casaLegislativaEnum, cargoParlamentarEnum } from "@/types/mandato.types";
import { Button } from "@/components/ui/button";
import { MultiSelect } from "@/components/multiselect/multiselect";
import { DatePickerRange } from "@/components/ui/datepicker-range";
import { DateRange } from "react-day-picker";

interface FiltersProps {
  cargo_parlamentar: string[];
  casa_legislativa: string[];
  partido: string[];
  perfil_parlamentar: string[];
  espectro_politico: string[];
  dateRange: DateRange | undefined;
  onDateRangeChange: (dateRange: DateRange | undefined) => void;
  onCargoParlamentarChange: (cargo: string[]) => void;
  onCasaLegislativaChange: (casa: string[]) => void;
  onPartidoChange: (partido: string[]) => void;
  onPerfilParlamentarChange: (perfil: string[]) => void;
  onEspectroPoliticoChange: (espectro: string[]) => void;
}

export function Filters({
  cargo_parlamentar,
  casa_legislativa,
  partido,
  perfil_parlamentar,
  espectro_politico,
  dateRange,
  onDateRangeChange,
  onCargoParlamentarChange,
  onCasaLegislativaChange,
  onPartidoChange,
  onPerfilParlamentarChange,
  onEspectroPoliticoChange,
}: FiltersProps) {
  const hasFilters = cargo_parlamentar.length > 0 ||
    casa_legislativa.length > 0 ||
    partido.length > 0 ||
    perfil_parlamentar.length > 0 ||
    espectro_politico.length > 0 ||
    dateRange;
  // Opções para o filtro de cargo parlamentar
  const cargoParlamentarOptions = Object.values(cargoParlamentarEnum).map(cargo => ({
    value: cargo,
    label: cargo
  }));

  // Opções para o filtro de casa legislativa
  const casaLegislativaOptions = Object.values(casaLegislativaEnum).map(casa => ({
    value: casa,
    label: casa
  }));

  // Opções para o filtro de partido político
  const partidoPoliticoOptions = partidosPoliticosTSE.map(partido => ({
    value: partido.sigla,
    label: partido.nome
  }));

  // Opções para o filtro de perfil parlamentar
  const perfilParlamentarOptions = PERFIS_MANDATO.map(perfil => ({
    value: perfil.value,
    label: perfil.label
  }));

  // Opções para o filtro de posicionamento do mandato
  const posicionamentoMandatoOptions = Object.values(POSICIONAMENTO_MANDATO).map(posicionamento => ({
    value: posicionamento,
    label: posicionamento
  }));

  return (
    <div className="grid grid-cols-[1fr_auto] gap-4 items-start">

      <div className="flex gap-2 flex-wrap">
        <div className="min-w-[200px]">
          <MultiSelect
            placeholder="Cargo Parlamentar"
            options={cargoParlamentarOptions}
            defaultValue={cargo_parlamentar}
            onValueChange={onCargoParlamentarChange}
            maxCount={2}
          />
        </div>
        <div className="min-w-[200px]">
          <MultiSelect
            placeholder="Casa Legislativa"
            options={casaLegislativaOptions}
            defaultValue={casa_legislativa}
            onValueChange={onCasaLegislativaChange}
            maxCount={2}
          />
        </div>
        <div className="min-w-[200px]">
          <MultiSelect
            placeholder="Partido Político"
            options={partidoPoliticoOptions}
            defaultValue={partido}
            onValueChange={onPartidoChange}
            maxCount={2}
          />
        </div>
        <div className="min-w-[200px]">
          <MultiSelect
            placeholder="Perfil"
            options={perfilParlamentarOptions}
            defaultValue={perfil_parlamentar}
            onValueChange={onPerfilParlamentarChange}
            maxCount={2}
          />
        </div>
        <div className="min-w-[200px]">
          <MultiSelect
            placeholder="Posicionamento"
            options={posicionamentoMandatoOptions}
            defaultValue={espectro_politico}
            onValueChange={onEspectroPoliticoChange}
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
            onCargoParlamentarChange([]);
            onCasaLegislativaChange([]);
            onPartidoChange([]);
            onPerfilParlamentarChange([]);
            onEspectroPoliticoChange([]);
            onDateRangeChange(undefined);
          }}>
            Limpar filtros
          </Button>
        </div>
      )}
    </div>
  );
}