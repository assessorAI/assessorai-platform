import { AppThrowError } from '../error/app-throw-error';
import { REGISTER_PATH, RegisterRequest } from './register.types'
import { NextRequest, NextResponse } from "next/server"
import { handleApiError } from '../error/error.handler';

const prepareBodyRequest = async (req: NextRequest) => {
  try {
    const userData = await req.json() as RegisterRequest;
    return JSON.stringify(userData);
  } catch {
    throw new AppThrowError(500, "internal", "Erro ao preparar o corpo da requisição");
  }
}

export async function register(req: NextRequest) {
  try {
    const body = await prepareBodyRequest(req);

    const { searchParams } = new URL(req.url);

    const queryString = searchParams.toString();
    const registerUrl = queryString ? `${REGISTER_PATH}?${queryString}` : REGISTER_PATH;

    const response = await fetch(registerUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    })

    if (!response.ok) {
      throw await AppThrowError.fromFetchResponse(response, "external");
    }

    return NextResponse.json({ message: 'Usuário criado com sucesso' })
  } catch (error) {
    return handleApiError(error);
  }
}