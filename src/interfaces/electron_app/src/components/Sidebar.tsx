import { useNavigate, useLocation } from "react-router-dom"
import { Sparkles } from "lucide-react"
import {
  Sidebar as SidebarComponent,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from "./ui/sidebar"
import { Badge } from "./ui/badge"
import { navigationItems, aiCategories } from "../config/sidebar"

export function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'maintenance': return 'bg-yellow-500'
      case 'beta': return 'bg-blue-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <SidebarComponent className="border-r bg-background/50 backdrop-blur-sm">
      <SidebarHeader className="p-4">
        <div className="flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-blue-600" />
          <span className="font-semibold">AI Services</span>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigationItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    onClick={() => navigate(item.url)}
                    isActive={location.pathname === item.url}
                    className="hover:bg-accent/50 transition-colors"
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {aiCategories.map((category) => (
          <SidebarGroup key={category.title}>
            <SidebarGroupLabel className="flex items-center gap-2">
              <category.icon className="h-4 w-4" />
              {category.title}
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {category.services.map((service) => (
                  <SidebarMenuItem key={service.id}>
                    <SidebarMenuButton
                      onClick={() => navigate(`/service/${service.id}`)}
                      isActive={location.pathname === `/service/${service.id}`}
                      className="hover:bg-accent/50 transition-colors"
                    >
                      <div className={`h-2 w-2 rounded-full ${getStatusColor(service.status)}`} />
                      <span className="flex-1">{service.name}</span>
                      {service.status === 'beta' && (
                        <Badge variant="secondary" className="text-xs">Beta</Badge>
                      )}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter className="p-4">
        <div className="text-xs text-muted-foreground">
          <div>API Usage: 1,234 / 10,000</div>
          <div className="w-full bg-secondary rounded-full h-1 mt-1">
            <div className="bg-blue-600 h-1 rounded-full" style={{ width: '12.34%' }} />
          </div>
        </div>
      </SidebarFooter>
    </SidebarComponent>
  )
}
