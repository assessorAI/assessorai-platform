export type DocumentosCasa = {
    id: string
    filename: string
    file_type: DocumentosCasaFileType
    title: string
}

export type DocumentosCasaResponse = {
    files: DocumentosCasa[]
}

export enum DocumentosCasaFileType {
    CONSTITUICAO = "Constituição",
    REGIMENTO_INTERNO = "Regimento Interno",
    OUTRO = "Outro",
}