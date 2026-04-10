import { FormDataRegister } from "@/features/auth/register/register-step.context";
import { buildRegisterRequest } from "./register.service";

/**
 * Serviço criado para criar um novo usuário a partir do ADM. 
 * Ele se diferencia do register.service porque o usuário é criado a partir do ADM e não do usuário.
 * Dessa forma, ele recebe o id do mandato selecionado e não é criado um mandato no fluxo padrão.
 */
export const userService = {
    create: async (formData: FormDataRegister) => {
        const request = buildRegisterRequest(formData);
        request.mandato = [{ id: formData.mandato!.id }];

        if (!request.password) {
            delete request.password;
        }

        const response = await fetch(`/api/user`, {
            method: 'POST',
            body: JSON.stringify(request),
        });

        if (!response.ok) throw new Error(`Erro ao registrar usuário: ${response.status} ${response.statusText}`);
        return response.json();
    },
};
