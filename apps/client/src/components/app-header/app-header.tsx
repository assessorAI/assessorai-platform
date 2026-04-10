import Link from "next/link";

import { Button } from "../ui/button";
import { AppBreadcrumb } from "../app-breadcrumb/app-breadcrumb";
import { AppHeaderProps } from "./app-header.types";

import "./app-header.scss"

export function AppHeader({ title, actions = [], breadcrumb = [], description = "" }: AppHeaderProps) {
  const hasBreadcrumb = breadcrumb.length > 0;

  return (
    <div className="app-header">
      <div className="app-header-breadcrumb">
        {hasBreadcrumb && <AppBreadcrumb breadcrumb={breadcrumb} />}
      </div>

      <div className="app-header-content">
        <h1>{title}</h1>
        <div className="app-header-actions">
          {actions.map((action, index) => (
            <Button
              asChild
              key={action.label}
              variant={index === actions.length - 1 ? "default" : "outline"}
              className="app-header-actions-button"
              aria-label={action.label}
              tabIndex={0}
            >
              <Link href={action.link}>
                {action.icon}
                <span className="text-brand-primary-text-bold">{action.label}</span>
              </Link>
            </Button>
          ))}
        </div>
      </div>

      <div className="app-header-description">
        <p>{description}</p>
      </div>
    </div>
  )
}