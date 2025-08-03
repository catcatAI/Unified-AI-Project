import { 
  Home, 
  MessageSquare, 
  Network, 
  Gamepad2, 
  Code, 
  History, 
  Workflow, 
  Settings,
  Brain,
  Bot,
  Cpu
} from "lucide-react";

export const navigationItems = [
  {
    title: "Dashboard",
    url: "/",
    icon: Home,
  },
  {
    title: "Chat",
    url: "/chat",
    icon: MessageSquare,
  },
  {
    title: "HSP Network",
    url: "/hsp",
    icon: Network,
  },
  {
    title: "Game",
    url: "/game",
    icon: Gamepad2,
  },
  {
    title: "Code Analysis",
    url: "/code-analysis",
    icon: Code,
  },
  {
    title: "History",
    url: "/history",
    icon: History,
  },
  {
    title: "Workflows",
    url: "/workflows",
    icon: Workflow,
  },
  {
    title: "Settings",
    url: "/settings",
    icon: Settings,
  },
];

export const aiCategories = [
  {
    title: "AI Services",
    icon: Brain,
    services: [
      {
        id: "llm-chat",
        name: "LLM Chat",
        status: "active",
      },
      {
        id: "code-analysis",
        name: "Code Analysis",
        status: "active",
      },
      {
        id: "image-gen",
        name: "Image Generation",
        status: "beta",
      },
    ],
  },
  {
    title: "Automation",
    icon: Bot,
    services: [
      {
        id: "workflow-engine",
        name: "Workflow Engine",
        status: "active",
      },
      {
        id: "task-scheduler",
        name: "Task Scheduler",
        status: "maintenance",
      },
    ],
  },
  {
    title: "System",
    icon: Cpu,
    services: [
      {
        id: "resource-monitor",
        name: "Resource Monitor",
        status: "active",
      },
      {
        id: "health-check",
        name: "Health Check",
        status: "active",
      },
    ],
  },
];