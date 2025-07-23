import { Outlet } from "react-router-dom"
import { Header } from "./Header"
import { Sidebar } from "./Sidebar"
import { Footer } from "./Footer"
import { SidebarProvider } from "./ui/sidebar"

export function Layout() {
  return (
    <SidebarProvider>
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-secondary/20">
        <Header />
        <div className="flex h-[calc(100vh-4rem)] pt-16">
          <Sidebar />
          <main className="flex-1 overflow-y-auto">
            <div className="p-6">
              <Outlet />
            </div>
          </main>
        </div>
        <Footer />
      </div>
    </SidebarProvider>
  )
}