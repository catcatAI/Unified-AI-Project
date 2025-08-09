import {
  MessageSquare,
  Image,
  Mic,
  BarChart3,
  Code,
  Wrench,
  Home,
  History,
  Workflow,
  Settings,
  Sparkles,
  Languages,
  Eye,
  Volume2,
  Database,
  Gamepad2,
  Network
} from "lucide-react"

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
    title: "Workflows",
    url: "/workflows",
    icon: Workflow,
  },
  {
    title: "Settings",
    url: "/settings",
    icon: Settings,
  },
  {
    title: "Atlassian",
    url: "/atlassian",
    icon: Network,
  },
]

export const aiCategories = [
  {
    title: "Text & Language",
    icon: MessageSquare,
    services: [
      { name: "GPT-4", id: "gpt-4", status: "active" },
      { name: "Claude", id: "claude", status: "active" },
      { name: "Translation", id: "translation", status: "active" },
      { name: "Summarization", id: "summarization", status: "active" },
    ]
  },
  {
    title: "Image & Vision",
    icon: Image,
    services: [
      { name: "DALL-E 3", id: "dalle-3", status: "active" },
      { name: "Stable Diffusion", id: "stable-diffusion", status: "active" },
      { name: "Image Analysis", id: "image-analysis", status: "active" },
      { name: "Image Editing", id: "image-editing", status: "maintenance" },
    ]
  },
  {
    title: "Audio & Speech",
    icon: Mic,
    services: [
      { name: "Whisper", id: "whisper", status: "active" },
      { name: "Text-to-Speech", id: "tts", status: "active" },
      { name: "Voice Clone", id: "voice-clone", status: "beta" },
    ]
  },
  {
    title: "Data & Analytics",
    icon: BarChart3,
    services: [
      { name: "Data Processing", id: "data-processing", status: "active" },
      { name: "Chart Generation", id: "chart-generation", status: "active" },
      { name: "Insights", id: "insights", status: "active" },
    ]
  },
  {
    title: "Code & Development",
    icon: Code,
    services: [
      { name: "Code Generation", id: "code-generation", status: "active" },
      { name: "Code Review", id: "code-review", status: "active" },
      { name: "Debugging", id: "debugging", status: "active" },
    ]
  },
]
