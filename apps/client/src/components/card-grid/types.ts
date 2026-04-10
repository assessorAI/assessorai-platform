import { ReactNode } from 'react'
import { BrandColor } from '@/types/brand-color.types'

// Interface para cada card individual
export interface CardGridItem {
  title: string
  description: string
  icon: ReactNode  
  iconSolid: ReactNode   
  link: string
  color?: BrandColor
}

// Props principais do componente CardGrid
export interface CardGridProps {
  title: string
  cards: CardGridItem[]
} 