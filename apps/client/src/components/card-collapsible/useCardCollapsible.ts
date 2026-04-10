import { useCallback, useState } from "react";

export const useCardCollapsible = (defaultOpen: boolean) => {
  const [value, setValue] = useState<string | undefined>(
    defaultOpen ? "item-1" : undefined
  );

  const onClick = (v: string | undefined) => {
    setValue(v);
  };

  const closeAccordion = useCallback(() => {
    setValue(undefined);
  }, []);

  const openAccordion = useCallback(() => {
    setValue("item-1");
  }, []);

  return { accordionValue: value, onClickAccordion: onClick, closeAccordion, openAccordion };
};