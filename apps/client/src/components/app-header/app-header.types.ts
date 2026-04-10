import { BreadcrumbItem } from "../app-breadcrumb/breadcrumb.types"

export interface HeaderActions {
  link: string
  label: string
  icon: React.ReactNode
}

export type AppHeaderProps = {
  title?: string
  actions?: HeaderActions[]
  breadcrumb?: BreadcrumbItem[]
  description?: string
}