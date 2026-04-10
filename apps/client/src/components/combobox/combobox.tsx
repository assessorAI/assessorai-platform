"use client"

import * as React from "react"
import { Check, ChevronDown } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

import styles from "./combobox.module.scss"

export type ComboboxProps = {
  items: { value: string, label: string }[],
  value: string,
  onChange: (value: string) => void,
  disabled?: boolean,
  readOnly?: boolean,
  placeholder?: string
}

export function Combobox({ items, value, onChange, disabled, readOnly, placeholder }: ComboboxProps) {
  const [open, setOpen] = React.useState(false)

  const handleSelect = (selectedValue: string) => {
    const item = items.find(
      (item) => item.label.toLowerCase() === selectedValue.toLowerCase()
    )
    if (item) {
      onChange(item.value)
      setOpen(false)
    }
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={styles.comboboxTrigger}
          disabled={disabled || readOnly}
          aria-readonly={readOnly}
        >
          {value
            ? items.find((item) => item.value === value)?.label
            : (placeholder ?? "Selecione uma opção")}
          <ChevronDown className={styles.comboboxIcon} />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="lg:w-full sm:w-[200px] p-0" align="start">
        <Command>
          <CommandInput placeholder="Pesquisar..." className={styles.comboboxInput} />
          <CommandList>
            <CommandEmpty className={styles.comboboxEmpty}>Nenhuma opção encontrada.</CommandEmpty>
            <CommandGroup>
              {items.map((item) => (
                <CommandItem
                  key={item.value}
                  value={item.label}
                  onSelect={handleSelect}
                >
                  {item.label}
                  <Check
                    className={cn(
                      "ml-auto",
                      value === item.value ? "opacity-100" : "opacity-0"
                    )}
                  />
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
