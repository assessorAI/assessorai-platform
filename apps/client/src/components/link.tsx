import Link from "next/link"

export const CustomLink = ({ href, children }: { href: string, children: React.ReactNode }) => {
  return (
    <Link href={href} className="text-black font-semibold hover:text-brand-accent hover:underline">
      {children}
    </Link>
  )
}