import { FormDataRegister } from "./register-member-step.context";

export const registerMemberService = {
  registerMember: async (formData: FormDataRegister) => {
    const response = await fetch(`/api/register-member`, {
      method: 'POST',
      body: JSON.stringify(formData),
    });
    if (!response.ok) throw new Error(`Erro ao registrar usuário: ${response.status} ${response.statusText}`);
    return response.json();
  },
};