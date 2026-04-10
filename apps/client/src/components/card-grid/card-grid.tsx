import Link from "next/link"
import { Card, CardDescription, CardHeader } from "@/components/ui/card"
import { CardGridProps } from "./types"

import styles from "./card-grid.module.scss"
import { BrandColor } from "@/types/brand-color.types"

export const CardGrid = ({
  title,
  cards,
}: CardGridProps) => {
  const defaultColor = BrandColor.ACCENT;

  return (
    <div className={styles.cardGrid}>
      <h2 className={styles.cardGridTitle}>{title}</h2>

      <div className={styles.cardGridCards}>

        {cards.map((card) => (
          <Link href={card.link} key={card.title}>

            <Card className={`${styles.card} group`}>

              <CardHeader className={styles.cardGridCardHeader}>

                <div className={`${styles.cardGridCardIconContainer} ${styles[`cardGridCardIconContainer${card.color || defaultColor}`]}`}>
                  <span className="group-hover:hidden">
                    {card.icon}
                  </span>
                  
                  <span className="hidden group-hover:block">
                    {card.iconSolid}
                  </span>
                </div>

                <h3 className="lead-title">{card.title}</h3>

                <CardDescription className={styles.cardGridCardDescription}>
                  {card.description}
                </CardDescription>

              </CardHeader>

            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
} 