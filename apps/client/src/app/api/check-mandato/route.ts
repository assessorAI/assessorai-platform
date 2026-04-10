import { NextRequest } from 'next/server'
import { checkMandato } from '@/api/register/check-mandato/check-mandato.handler'

export async function POST(req: NextRequest) {
  return await checkMandato(req)
} 