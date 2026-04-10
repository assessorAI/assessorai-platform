export function isExpiredDate(expiresAt: string) {
    const now = new Date()
    const expiresAtDate = new Date(expiresAt)
    // Diminui 3 horas como margem de segurança com relação ao horário do servidor
    expiresAtDate.setHours(expiresAtDate.getHours() - 3)
    return  now >= expiresAtDate;
}