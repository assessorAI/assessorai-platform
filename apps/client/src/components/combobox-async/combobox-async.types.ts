export interface ComboboxOption {
    value: string;
    label: string;
}

export interface PaginatedResponse<T> {
    data: T[];
    total: number;
    offset: number;
    limit: number;
    hasMore: boolean;
}

export type FetchFunction<T> = (params: {
    search: string;
    offset: number;
    limit: number;
}) => Promise<PaginatedResponse<T>>;


/**
 * Props para o ComboboxAsync
 * @param fetchOptions - Função que busca os dados
 * @param getOptionLabel - Função que transforma o item T em label (texto exibido)
 * @param getOptionValue - Função que retorna um ID único do item (usado para comparação)
 * @param value - Objeto selecionado (T | null)
 * @param onValueChange - Função que recebe o objeto selecionado ou null
 * @param placeholder - Texto de placeholder
 * @param emptyText - Texto quando não há resultados
 * @param queryKey - Chave única para o React Query cache
 * @param pageSize - Número de itens por página
 */
export interface ComboboxAsyncProps<T> {
    // Função que busca os dados
    fetchOptions: FetchFunction<T>;

    // Função que transforma o item T em label (texto exibido)
    getOptionLabel: (item: T) => string;
    
    // Função que retorna um ID único do item (usado internamente para comparação)
    getOptionValue: (item: T) => string;

    // Valor selecionado - agora é o objeto completo ou null
    value?: T | null;
    onValueChange?: (value: T | null) => void;

    // UI
    placeholder?: string;
    emptyText?: string;

    // Chave única para o React Query cache
    queryKey: string[];

    // Número de itens por página
    pageSize?: number;
    disabled?: boolean;
    readOnly?: boolean;
}