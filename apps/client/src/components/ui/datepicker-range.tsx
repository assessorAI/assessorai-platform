"use client"
import * as React from "react"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Label } from "@/components/ui/label"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { format } from "date-fns"
import { CalendarIcon } from "lucide-react"
import { type DateRange } from "react-day-picker"
import { ptBR as ptBRLocale } from "date-fns/locale"
import { useEffect } from "react";

export type DatePickerRangeProps = {
  label?: string
  placeholder?: string
  value?: DateRange | undefined
  onChange: (value: DateRange | undefined) => void
}

/**
 * DatePickerWithRange é um componente que permite selecionar um período de data.
 * @param label - O label do componente.
 * @param placeholder - O placeholder do componente.
 * @param value - O valor do componente.
 * @param onChange - A função que será chamada quando o valor for alterado.
 * 
 * @example
 * <DatePickerRange
 *  label="Período de acesso"
 *  placeholder="Selecione o período de acesso"
 *  value={{
 *    from: new Date(),
 *    to: new Date(),
 *  }}
 *  onChange={(value) => { console.log(value) }}
 */
export function DatePickerRange({ label, placeholder, value, onChange }: DatePickerRangeProps) {
  const [internalDate, setInternalDate] = React.useState<DateRange | undefined>({
    from: undefined,
    to: undefined,
  })

  // Extraindo os valores de tempo para variáveis separadas (evita expressões complexas no array de dependências)
  const fromTime = value?.from?.getTime();
  const toTime = value?.to?.getTime();

  useEffect(() => {
    setInternalDate(value);
  }, [value, fromTime, toTime]);

  const date = value || internalDate;

  const handleDateChange = (newDate: DateRange | undefined) => {
    setInternalDate(newDate);


    if (newDate?.from && newDate?.to && (newDate.from < newDate.to)) {
      onChange({
        from: newDate.from,
        to: newDate.to,
      });
    }
  }

  return (
    <div>
      {label && <Label htmlFor="date-picker-range">{label}</Label>}
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            id="date-picker-range"
            className="justify-start w-full h-10 rounded-md hover:rounded-md focus:rounded-md border-brand-border"
          >
            <CalendarIcon />
            {date?.from ? (
              date.to ? (
                <>
                  {format(date.from, "LLL dd, y", { locale: ptBRLocale })} -{" "}
                  {format(date.to, "LLL dd, y", { locale: ptBRLocale })}
                </>
              ) : (
                format(date.from, "LLL dd, y", { locale: ptBRLocale })
              )
            ) : (
              <span className="text-brand-placeholder">{placeholder}</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="range"
            defaultMonth={date?.from}
            selected={date}
            onSelect={handleDateChange}
            numberOfMonths={2}
            locale={ptBRLocale}
          />
        </PopoverContent>
      </Popover>
    </div>
  )
}
