const BASE_URL = process.env.BACKEND_ASSESSORAI_URL;

export const ENDPOINTS: Record<string, Record<string, string>> = {
  ADM: {
    SUMMARY: `${BASE_URL}/admin/summary`,
    SEND_PASSWORD_RESET: `${BASE_URL}/admin/send-password-reset`,
  },
  AUTH: {
    REGISTER: `${BASE_URL}/auth/register`,
    LOGIN: `${BASE_URL}/auth/login`,
    CHECK_EMAIL: `${BASE_URL}/validation/email`,
    CHECK_MANDATO: `${BASE_URL}/validation/mandato`,
    FORGOT_PASSWORD: `${BASE_URL}/auth/forgot-password`,
    RESET_PASSWORD: `${BASE_URL}/auth/reset-password`,
    ACTIVATE_ACCOUNT: `${BASE_URL}/auth/activate`,
  },
  EMENDA: {
    CREATE: `${BASE_URL}/expert/pl/criar_emenda`,
  },
  ANALISE_CONSTITUCIONALIDADE: {
    CREATE: `${BASE_URL}/expert/pl/analise_constitucionalidade`,
  },
  CRIAR_PL: {
    CREATE: `${BASE_URL}/expert/pl/criar_projeto`,
  },
  REQUERIMENTO: {
    CREATE: `${BASE_URL}/oficio/generate`,
  },
  SUGESTAO_EMENDAS: {
    CREATE: `${BASE_URL}/expert/pl/sugestao_emendas`,
  },
  BUSCA_REFERENCIAS: {
    GET: `${BASE_URL}/search/query`,
  },
  BUSCA_UF: {
    GET: `https://servicodados.ibge.gov.br/api/v1/localidades/estados`,
  },
  BUSCA_MUNICIPIOS: {
    GET: `https://servicodados.ibge.gov.br/api/v1/localidades/estados/{UF}/municipios`,
  },
  MANDATO: {
    GET_ALL: `${BASE_URL}/mandatos/`,
    UPDATE: `${BASE_URL}/mandatos/{id}`,
    GET: `${BASE_URL}/mandatos/{id}`,
    ADD_USER: `${BASE_URL}/mandatos/{id}/users`,
    DELETE_USER: `${BASE_URL}/mandatos/{id}/users/{userId}`,
    ADD_DOCUMENT: `${BASE_URL}/files/upload`,
    GET_DOCUMENTS: `${BASE_URL}/files/list`,
    DELETE_DOCUMENT: `${BASE_URL}/files/delete/{file_id}`,
    DOWNLOAD_DOCUMENT: `${BASE_URL}/files/{file_id}/content`,
    USERS: `${BASE_URL}/mandatos/{mandato_id}/users`,
    DELETE: `${BASE_URL}/mandatos/{id}`,
  },
  USER: {
    GET: `${BASE_URL}/user/{id}`,
    POST: `${BASE_URL}/user/`,
    GET_ALL: `${BASE_URL}/user/`,
    PUT: `${BASE_URL}/user/{id}`,
    DELETE: `${BASE_URL}/user/{id}`,
  },
} as const;
