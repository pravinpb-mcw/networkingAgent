import * as React from "react"
import {
  LayoutDashboard,
  Bot,
  Activity,
  Sliders
} from "lucide-react"
import { useNavigate, useLocation } from 'react-router-dom'

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"

const data = {
  navMain: [
    {
      title: "Dashboard",
      url: "/",
      icon: LayoutDashboard,
    },
    {
      title: "AI Analysis",
      url: "/ai-analysis",
      icon: Bot,
    },
    {
      title: "Phoenix Traces",
      url: "/phoenix",
      icon: Activity,
    },
    {
      title: "Controls",
      url: "/controls",
      icon: Sliders,
    },
  ],
  navSecondary: [],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground">
              <div className="hidden aspect-square size-8 items-center justify-center rounded-lg overflow-hidden bg-black dark:bg-transparent p-1.5 group-data-[collapsible=icon]:flex">
                <img src="/favicon.png" alt="NetAgent Icon" className="w-full h-full object-contain" />
              </div>
              <div className="flex w-full items-center justify-center rounded-lg bg-black dark:bg-transparent px-4 py-2 group-data-[collapsible=icon]:hidden">
                <img src="/logo-1.png" alt="NetAgent Logo" className="h-8 w-auto object-contain" />
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Platform</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {data.navMain.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    tooltip={item.title}
                    isActive={location.pathname === item.url}
                    onClick={() => navigate(item.url)}
                  >
                    <a>
                      <item.icon />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg">
              <div className="grid flex-1 text-left text-xs leading-tight">
                <span className="truncate font-medium">Admin User</span>
                <span className="truncate text-xs">admin@netagent.local</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
