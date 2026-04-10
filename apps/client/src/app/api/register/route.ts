import { NextRequest } from 'next/server'
import { register } from '@/api/register/register'

export async function POST(req: NextRequest) {
  return await register(req)
} 