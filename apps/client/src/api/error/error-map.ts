export const errorMap = {
    400: 'Dados inválidos. Verifique as informações e tente novamente.',
    401: 'Sessão expirada. Por favor, faça login novamente.',
    403: 'Você não tem permissão para realizar esta ação.',
    404: 'Recurso não encontrado.',
    408: 'Tempo de requisição esgotado. Tente novamente.',
    422: 'Dados fornecidos não puderam ser processados.',
    429: 'Muitas tentativas. Aguarde alguns instantes e tente novamente.',
    500: 'Erro interno do servidor. Tente novamente mais tarde.',
    502: 'Serviço temporariamente indisponivel. Tente novamente.',
    503: 'Erro de conexão. Verifique sua internet e tente novamente.',
    504: 'Tempo de resposta do servidor esgotado. Tente novamente.',
  };
  
  export const friendlyErrorMessage = {
      EMAIL_ALREADY_IN_USE: `Esse email já possui cadastro na Assessoraí.`,
      EMAIL_ALREADY_IN_USE_TEAM: `Esse email já foi convidado para fazer parte de uma equipe dentro do Assessoraí.
      Verifique o link recebido por email.`,
      EMAIL_CHECK_ERROR: `Erro ao verificar email.`,
      MANDATO_ALREADY_EXISTS: `Uma mandato com as informações preenchidas anteriormente já foi cadastrado
      na Assessoraí. Verifique com sua equipe e solicite um convite para acessar a conta criada.`,
      ERRO_DESCONHECIDO: `Erro desconhecido.`,
  }