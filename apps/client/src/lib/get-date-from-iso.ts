/**
 * Converte uma data no formato ISO (ex: 2026-01-16T20:22:29.081319) 
 * para o formato brasileiro DD/MM/YYYY (ex: 16/01/2026)
 * 
 * @param isoDate - String da data no formato ISO
 * @returns String da data formatada no padrão brasileiro DD/MM/YYYY
 */
export const getDateFromIso = (isoDate: string): string => {

    if (!isoDate) return "";

    const date = new Date(isoDate);

    const day = date.getDate();
    const month = date.getMonth() + 1;
    const year = date.getFullYear();
    
    const formattedDay = day.toString().padStart(2, '0');
    const formattedMonth = month.toString().padStart(2, '0');
    
    return `${formattedDay}/${formattedMonth}/${year}`;
  };