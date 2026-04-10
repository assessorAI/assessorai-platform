import { NextRequest } from 'next/server'
import { checkEmail } from '@/api/register/check-email/check-email.handler'

export async function GET(req: NextRequest) {
  return await checkEmail(req)
} 