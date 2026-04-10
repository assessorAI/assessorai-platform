import { dadosPessoais } from "@/types/schemas/dados-pessoais.schema";
import { dadosMandato } from "@/types/schemas/dados-mandato.schema";
import { perfilMandato } from "@/types/schemas/perfil_mandato.schema";
import { crieSenha } from "@/types/schemas/crie-senha.schema";
import { createStepContext } from "@/context/step-form.context";
import type { Mandato } from "@/api/mandato/mandato.types";

export type FormDataRegister = dadosPessoais & dadosMandato & perfilMandato & crieSenha & {
    mandato?: Mandato | null
};

const { StepProvider: RegisterStepProvider, useStep } = createStepContext<FormDataRegister>();

export { RegisterStepProvider, useStep };