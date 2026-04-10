import { useEffect, useState } from 'react';

export const useDebounce = <T,>(value: T, delay: number = 300): T => {
  // Estado que armazena o valor com delay
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Cria um timer que vai atualizar o valor depois do delay
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Limpa o timer se o valor mudar antes do delay acabar
    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
};