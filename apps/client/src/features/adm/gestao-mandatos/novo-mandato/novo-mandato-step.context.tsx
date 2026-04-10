import { createStepContext } from "@/context/step-form.context";
import { dadosMandato } from "@/types/schemas/dados-mandato.schema";
import { perfilMandato } from "@/types/schemas/perfil_mandato.schema";
import { crieSenha } from "@/types/schemas/crie-senha.schema";
import { dadosPessoais } from "@/types/schemas/dados-pessoais.schema";

export type FormDataNovoMandato = dadosPessoais & dadosMandato & perfilMandato & crieSenha;

const { StepProvider: NovoMandatoStepProvider, useStep: useNovoMandatoStep } = 
  createStepContext<FormDataNovoMandato>();

export { NovoMandatoStepProvider, useNovoMandatoStep };