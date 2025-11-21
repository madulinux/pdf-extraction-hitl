/**
 * Main App Layout
 * Layout with sidebar for authenticated pages
 */
'use client';

import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex-1 w-full">
        <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="flex h-14 items-center px-4">
            <SidebarTrigger />
          </div>
        </div>
        <div className="flex-1 space-y-4 p-8 pt-6">
          {children}
        </div>
      </main>
    </SidebarProvider>
  );
}
