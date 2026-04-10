import { RegisterRequest } from "@/api/register/register.types";
import { FormDataRegister } from "../features/auth/register/register-step.context";
import { PermissionLevel } from "@/types/user.types";
import { MandatoRequest } from "@/api/register/register.types";

export const registerService = {
  register: async (formData: FormDataRegister, utmParams?: string) => {
    const request = buildRegisterRequest(formData);
    const mandato = buildMandato(formData);

    request.mandato = mandato;

    const url = utmParams ? `/api/register?${utmParams}` : `/api/register`;

    const response = await fetch(url, {
      method: 'POST',
      body: JSON.stringify(request),
    });

    if (!response.ok) throw new Error(`Erro ao registrar usuário: ${response.status} ${response.statusText}`);
    return response.json();
  },
};

export const buildRegisterRequest = (formData: FormDataRegister): Partial<RegisterRequest> => {
  return {
    email: formData.email,
    password: formData.password,
    first_name: formData.first_name,
    last_name: formData.last_name,
    phone: formData.phone,
    lgpd_check: formData.lgpd_check ? "true" : "false",
    permission_level: PermissionLevel.Manager,
    role: formData.role
  };
};

function buildMandato(formData: FormDataRegister): MandatoRequest[] {
  return [{
    nome_parlamentar: formData.nome_parlamentar,
    casa_legislativa: formData.casa_legislativa,
    municipio: formData.municipio,
    ue: formData.uf,
    perfil_parlamentar: formData.perfil_mandato,
    partido: formData.partido,
    espectro_politico: formData.posicionamento_mandato,
    cargo_parlamentar: formData.cargo_parlamentar,
  }];
}

export const getUtmParams = (searchParams: URLSearchParams) => {
  const utmParams = new URLSearchParams();

  searchParams.forEach((value: string, key: string) => {
    if (key.startsWith('utm_') || key.startsWith('rutm_')) {
      utmParams.append(key, value);
    }
  });

  return utmParams?.toString();
};

export const getRegisterUrl = (utmParams: string) => {
  return `/api/register?${utmParams}`;
};