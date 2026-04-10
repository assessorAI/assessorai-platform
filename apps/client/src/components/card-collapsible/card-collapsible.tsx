import { CardDescription, CardTitle } from "../ui/card";
import "./card-collapsible.scss";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "../ui/accordion";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../ui/tooltip";
import { InformationCircleIcon } from "@heroicons/react/24/outline";
import { CardCollapsibleProps, CardCollapsibleColor } from "./card-collapsible.types";
import { useCardCollapsible } from "./useCardCollapsible";

export function CardCollapsible({
  title,
  description,
  icon,
  tooltip,
  value,
  onValueChange,
  content,
  defaultOpen,
  color = CardCollapsibleColor.ACCENT
}: CardCollapsibleProps) {
  const { accordionValue, onClickAccordion } = useCardCollapsible(
    Boolean(defaultOpen)
  );
  const isControlled = typeof onValueChange === "function";
  const currentValue = isControlled ? value : accordionValue;
  const handleChange = isControlled ? onValueChange : onClickAccordion;

  return (
    <Accordion
      type="single"
      collapsible
      value={currentValue ?? ""}
      onValueChange={handleChange}
    >
      <AccordionItem value="item-1" className="accordion-item">
        <AccordionTrigger className="card-header">
          <div className={`card-header-icon card-header-icon-${color}`}>{icon}</div>
          <div className="card-header-content">
            <CardTitle className="card-header-title-container">
              <h2 className="card-header-title">{title}</h2>
              {tooltip && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="tooltip-trigger">
                        <InformationCircleIcon className="tooltip-trigger-icon" />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="right" className="tooltip-content">
                      <p>{tooltip}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </CardTitle>
            <CardDescription className="card-header-description">
              {description}
            </CardDescription>
          </div>
        </AccordionTrigger>
        <AccordionContent className="accordion-content">
          {content}
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
