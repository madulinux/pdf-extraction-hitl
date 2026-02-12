"use client";

import * as React from "react";
import { FileText, Database, Brain, Home } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from "@/components/ui/sidebar";
import { NavUser } from "./nav-user";
import { useAuthContext } from "@/contexts/AuthContext";

const menuItems = [
  {
    title: "Dashboard",
    url: "/dashboard",
    icon: Home,
  },
  {
    title: "Ekstraksi Data",
    url: "/extraction",
    icon: FileText,
  },
  {
    title: "Kelola Template",
    url: "/templates",
    icon: Database,
  },
  {
    title: "Pelatihan Model",
    url: "/training",
    icon: Brain,
  },
];

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const { user, logout } = useAuthContext();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <Sidebar>
      <SidebarHeader className="border-b px-6 py-4">
        <div className="flex items-center gap-2">
          <FileText className="w-6 h-6 text-primary" />
          <div>
            <h2 className="font-bold text-lg">PDF Extraction</h2>
            <p className="text-xs text-muted-foreground">
              Adaptive Learning System
            </p>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Menu Utama</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={pathname === item.url}>
                    <Link href={item.url}>
                      <item.icon className="w-4 h-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        {/* <div className="text-xs text-muted-foreground">
          <p className="font-medium">Adaptif Learning System</p>
          <p>based on Human-in-the-Loop (HITL)</p>
        </div> */}
        <NavUser
          user={{
            name: user?.full_name || "John Doe",
            email: user?.email || "john.doe@example.com",
            avatar: "https://github.com/johndoe.png",
          }}
          onLogout={handleLogout}
        />
      </SidebarFooter>
    </Sidebar>
  );
}
