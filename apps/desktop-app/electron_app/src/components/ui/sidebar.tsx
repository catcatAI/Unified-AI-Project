import React from "react";

export interface SidebarProps {
  className?: string;
  children: React.ReactNode;
}

export function Sidebar({ className = "", children }: SidebarProps) {
  return (
    <div className={`w-64 h-full ${className}`}>
      {children}
    </div>
  );
}

export function SidebarContent({ children }: { children: React.ReactNode }) {
  return <div className="flex-1 overflow-y-auto">{children}</div>;
}

export function SidebarHeader({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return <div className={`border-b ${className}`}>{children}</div>;
}

export function SidebarFooter({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return <div className={`border-t mt-auto ${className}`}>{children}</div>;
}

export function SidebarGroup({ children }: { children: React.ReactNode }) {
  return <div className="px-3 py-2">{children}</div>;
}

export function SidebarGroupLabel({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return <div className={`text-sm font-semibold text-gray-600 mb-2 ${className}`}>{children}</div>;
}

export function SidebarGroupContent({ children }: { children: React.ReactNode }) {
  return <div>{children}</div>;
}

export function SidebarMenu({ children }: { children: React.ReactNode }) {
  return <div className="space-y-1">{children}</div>;
}

export function SidebarMenuItem({ children }: { children: React.ReactNode }) {
  return <div>{children}</div>;
}

export interface SidebarMenuButtonProps {
  onClick?: () => void;
  isActive?: boolean;
  className?: string;
  children: React.ReactNode;
}

export function SidebarMenuButton({ onClick, isActive = false, className = "", children }: SidebarMenuButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-colors ${
        isActive 
          ? "bg-blue-100 text-blue-900" 
          : "text-gray-700 hover:bg-gray-100"
      } ${className}`}
    >
      {children}
    </button>
  );
}