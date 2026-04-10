import { auth, signOut } from "@/api/auth/index"
import { isProtectedRoute } from "@/config/routes"
import { isExpiredDate } from "./lib/is-expired-date";
import { PermissionLevel } from "./types/user.types";

export default auth((req) => {
  const { pathname } = req.nextUrl;

  if (pathname.startsWith("/adm") && req.auth?.user?.permission_level !== PermissionLevel.Admin) {
    return Response.redirect(new URL("/dashboard", req.nextUrl.origin))
  }

  if (isExpiredDate(req.auth?.expiresAt as string)) {
    signOut();
    return Response.redirect(new URL("/login", req.nextUrl.origin))
  }

  if (!req.auth?.accessToken && isProtectedRoute(pathname) && pathname !== "/login") {
    const newUrl = new URL("/login", req.nextUrl.origin)
    return Response.redirect(newUrl)
  }

  if (req.auth?.accessToken && pathname === '/login') {
    const newUrl = new URL("/dashboard", req.nextUrl.origin)
    return Response.redirect(newUrl)
  }

})

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|register|forgot-password|reset-password).*)"]
}