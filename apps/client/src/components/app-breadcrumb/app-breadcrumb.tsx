import React from "react";
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbSeparator } from "../ui/breadcrumb";

import { BreadcrumbItem as BreadcrumbItemInterface } from "./breadcrumb.types";
import { SlashIcon } from "@heroicons/react/24/outline";

export function AppBreadcrumb({ breadcrumb }: { breadcrumb: BreadcrumbItemInterface[] }) {
  return (
    breadcrumb && (
      <div className="app-header-breadcrumb">
        <Breadcrumb>
          <BreadcrumbList>
            {breadcrumb.map((item: BreadcrumbItemInterface, index: number) => (
              <React.Fragment key={index}>
                <BreadcrumbItem>
                  <BreadcrumbLink href={item.link}>
                    <span>{item.label}</span>
                  </BreadcrumbLink>
                </BreadcrumbItem>
                {index < breadcrumb.length - 1 && (
                  <BreadcrumbSeparator>
                    <SlashIcon />
                  </BreadcrumbSeparator>
                )}
              </React.Fragment>
            ))}
          </BreadcrumbList>
        </Breadcrumb>
      </div>
    )
  )
}