"use client";

import * as React from "react";
import { CheckIcon, XMarkIcon, ChevronDownIcon } from "@heroicons/react/24/outline";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useDebounce } from "@/hooks/useDebounce";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useEffect, useState, useRef, useMemo, useCallback } from "react";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ComboboxAsyncProps } from "./combobox-async.types";
import { Spinner } from "../ui/spinner";
import { PaginatedResponse } from "./combobox-async.types";
import styles from "./combobox-async.module.scss";


/**
 * Componente Combobox assíncrono com busca paginada e scroll infinito.
 * 
 * Permite buscar e selecionar itens de uma lista grande usando paginação no servidor,
 * com debounce automático na busca e carregamento incremental via scroll.
 * 
 * @template T - Tipo genérico do item que será exibido no combobox
 * 
 * @example
 *
 * interface Mandato {
 *   id: number;
 *   nome_parlamentar: string;
 * }
 * 
 * const [mandato, setMandato] = useState<Mandato | null>(null);
 * 
 * const buscarMandatos = async ({ search, offset, limit }) => {
 *   const res = await fetch(`/api/mandatos?offset=${offset}&limit=${limit}&search=${search}`);
 *   const data = await res.json();
 *   
 *   return {
 *     data: data.mandatos,
 *     total: data.total,
 *     offset: offset,
 *     limit: limit,
 *     hasMore: (offset + limit) < data.total,
 *   };
 * };
 * 
 * <ComboboxAsync<Mandato>
 *   fetchOptions={buscarMandatos}
 *   getOptionLabel={(m) => m.nome_parlamentar}
 *   getOptionValue={(m) => String(m.id)}
 *   value={mandato}
 *   onValueChange={setMandato}
 *   queryKey={["mandatos"]}
 *   placeholder="Selecione um mandato..."
 *   pageSize={20}
 * />
 */
export const ComboboxAsync = <T,>({
  fetchOptions,
  getOptionLabel,
  getOptionValue,
  value,
  onValueChange,
  placeholder = "Selecione...",
  emptyText = "Nenhum resultado encontrado",
  queryKey,
  pageSize = 20,
  disabled = false,
  readOnly = false,
}: ComboboxAsyncProps<T>) => {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const debouncedSearch = useDebounce(search, 300);

  // Ref para detectar scroll no fim da lista
  const observerTarget = useRef<HTMLDivElement>(null);

  // React Query para buscar dados com paginação
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteQuery({
    queryKey: [...queryKey, debouncedSearch], // Cache separado por busca
    queryFn: async ({ pageParam = 0 }) => {
      // Busca a página atual
      return await fetchOptions({
        search: debouncedSearch,
        offset: pageParam,
        limit: pageSize,
      });
    },
    getNextPageParam: (lastPage: PaginatedResponse<T>) => {
      // Calcula o próximo offset
      if (!lastPage.hasMore) return undefined;
      return lastPage.offset + lastPage.limit;
    },
    initialPageParam: 0,
    enabled: open, // Só busca quando o popover está aberto
  });

  const createScrollObserver = useCallback(() => {
    const currentTarget = observerTarget.current;

    if (!currentTarget) return;

    // Encontra o container com scroll (CommandList)
    const scrollContainer = currentTarget.closest('[cmdk-list]');

    if (!scrollContainer) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];

        const isVisible = entry.isIntersecting;
        const notLoading = !isFetchingNextPage;
        const toNextPage = isVisible && hasNextPage && notLoading;

        if (toNextPage) fetchNextPage();
      },
      {
        root: scrollContainer,
        rootMargin: '0px',
        threshold: 0.1,
      }
    );

    observer.observe(currentTarget);

    return () => {
      observer.unobserve(currentTarget);
      observer.disconnect();
    };
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  useEffect(() => {
    createScrollObserver();
  }, [createScrollObserver]);

  // Achatar todas as páginas em uma lista única
  const allOptions = useMemo(() => {
    const flattenedOptions = data?.pages ? data.pages.flatMap((page: { data: T[] }) => page.data) : [];

    // Se tem value (objeto selecionado) e ele não está nas opções carregadas, adiciona no início
    if (value) {
      const valueId = getOptionValue(value);
      const hasValue = flattenedOptions.some(
        (opt: T) => getOptionValue(opt) === valueId
      );

      if (!hasValue) {
        return [value, ...flattenedOptions];
      }
    }

    return flattenedOptions;
  }, [data, value, getOptionValue]);

  // Encontrar label do item selecionado
  const selectedLabel = useMemo(() => {
    if (!value) return placeholder;
    
    // Como value agora é o objeto completo, apenas extraímos o label
    return getOptionLabel(value);
  }, [value, placeholder, getOptionLabel]);

  return (
    <Popover open={open} onOpenChange={setOpen} modal={false}>
      <PopoverTrigger asChild>
        <Button
          disabled={disabled || readOnly}
          aria-readonly={readOnly}
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn(
            styles.comboboxTrigger,
            disabled && styles.comboboxTriggerDisabled,
            readOnly && styles.comboboxTriggerReadOnly
          )}
        >
          <span className="truncate">{selectedLabel}</span>
          <div className="flex items-center gap-1 ml-2">
            {value && (
              <span
                role="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onValueChange?.(null);
                }}
                className="h-4 w-4 opacity-50 hover:opacity-100 transition-opacity"
              >
                <XMarkIcon className="h-3 w-3" />
              </span>
            )}
            <ChevronDownIcon className="h-4 w-4 shrink-0 opacity-50" />
          </div>
        </Button>
      </PopoverTrigger>

      <PopoverContent
        className="p-0"
        align="start"
        style={{ width: 'var(--radix-popover-trigger-width)' }}
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <Command shouldFilter={false}> {/* Desabilita filtro local */}
          <CommandInput
            className="focus:outline-none"
            placeholder="Buscar..."
            value={search}
            onValueChange={setSearch}
          />

          <CommandList
            className="max-h-[300px] overflow-y-auto overflow-x-hidden"
            onWheel={(e) => {
              // Captura evento de scroll do touchpad/mouse
              e.stopPropagation();
            }}
            onTouchMove={(e) => {
              // Captura evento de touch em mobile
              e.stopPropagation();
            }}
          >
            {isLoading ? (
              <div className="py-6 text-center text-sm">
                <Spinner className="mx-auto h-4 w-4" />
              </div>
            ) : allOptions.length === 0 ? (
              <CommandEmpty className="p-3">{emptyText}</CommandEmpty>
            ) : (
              <CommandGroup>
                {allOptions.
                filter((option: T) => {
                  const label = getOptionLabel(option);
                  return label && label !== "null" && label.trim() !== "";
                })
                .map((option: T) => {
                  const optionValue = getOptionValue(option);
                  const optionLabel = getOptionLabel(option);
                  const isSelected = value && getOptionValue(value) === optionValue;

                  return (
                    <CommandItem
                      key={optionValue}
                      value={optionValue}
                      onSelect={() => {
                        // Se já está selecionado, limpa (null). Senão, seleciona o objeto completo
                        onValueChange?.(isSelected ? null : option);
                        setOpen(false);
                      }}
                    >
                      <CheckIcon
                        className={cn(
                          "mr-2 h-4 w-4",
                          isSelected ? "opacity-100" : "opacity-0"
                        )}
                      />
                      {optionLabel}
                    </CommandItem>
                  );
                })}

                {/* Elemento observado para scroll infinito */}
                <div ref={observerTarget} className="h-1" />

                {/* Loading da próxima página */}
                {isFetchingNextPage && (
                  <div className="py-2 text-center">
                    <Spinner className="mx-auto h-4 w-4" />
                  </div>
                )}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
};