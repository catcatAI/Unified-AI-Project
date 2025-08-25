# 🤖 AI Unified Dashboard (Frontend)

This application contains the main web-based AI dashboard for the Unified AI Project. It now integrates functionalities previously found in `frontend-quest`, providing a comprehensive interface for interacting with various AI services and tools.

## ✨ Features

### 🎯 Core AI Capabilities
- **💬 AI Chat** - Conversational AI interface with multiple model support
- **🎨 Image Generation** - Text-to-image generation with various size options
- **🔍 Web Search** - AI-powered web search and information retrieval
- **📝 Code Analysis** - Multi-language code quality analysis and optimization suggestions

### 🚀 Advanced Features
- **🤖 AI Agents** - Real-time agent management and task coordination
- **🧠 Neural Network** - Model training progress and performance monitoring
- **🔗 GitHub Connect** - Repository management and automation workflows
- **📊 System Monitor** - Real-time system metrics and performance analysis
- **Atlassian Integration** - Manage Jira issues and Confluence pages.
- **Rovo Dev Agents** - Interact with intelligent development agents.
- **🗄️ Data Archive** - Store and manage AI interaction history

### 🎨 User Experience
- **📱 Responsive Design** - Mobile-first approach with adaptive layouts
- **🌙 Dark/Light Mode** - Built-in theme switching support
- **⚡ Real-time Updates** - Live data updates with WebSocket support
- **🔔 Toast Notifications** - User-friendly feedback system

## 🛠️ Technology Stack

### Core Framework
- **⚡ Next.js 15** - React framework with App Router
- **📘 TypeScript 5** - Type-safe development
- **🎨 Tailwind CSS 4** - Utility-first CSS framework
- **🧩 shadcn/ui** - High-quality accessible components

### AI Integration
- **🤖 z-ai-web-dev-sdk** - AI model integration and tool access
- **🔌 Socket.IO** - Real-time communication
- **🌐 REST APIs** - Backend service integration (via proxy)

### State Management & UI
- **🐛 React Hooks** - State and lifecycle management
- **🎭 Lucide Icons** - Beautiful icon library
- **📊 Charts & Metrics** - Data visualization components

## 🚀 Quick Start

From the root of the monorepo (`Unified-AI-Project`):

```bash
pnpm --filter frontend-dashboard dev
```

This will start the development server for the frontend dashboard.

## 📁 Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── api/               # API routes
│   │   ├── chat/          # AI chat endpoint
│   │   ├── image/         # Image generation endpoint
│   │   ├── search/        # Web search endpoint
│   │   ├── code/          # Code analysis endpoint
│   │   └── health/        # Health check endpoint
│   ├── page.tsx           # Main page
│   └── layout.tsx         # Root layout
├── components/
│   ├── ai-dashboard/      # Dashboard components
│   │   ├── dashboard-layout.tsx
│   │   ├── sidebar.tsx
│   │   └── tabs/          # Individual tab components
│   └── ui/                # shadcn/ui components
├── hooks/                 # Custom React hooks
├── lib/                   # Utility functions
│   ├── utils.ts
│   ├── socket.ts          # Socket.IO configuration
│   └── db.ts              # Database configuration
└── quest-features/        # Features migrated from frontend-quest
    ├── components/
    ├── hooks/
    ├── lib/
    └── pages/
```

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file in the root directory of the monorepo:

```env
# AI Configuration (optional - scaffold provides defaults)
ZAI_API_KEY=your_zai_api_key
ZAI_API_BASE_URL=https://api.z.ai

# Database (optional - uses SQLite by default)
DATABASE_URL="file:./dev.db"

# GitHub Integration (optional)
GITHUB_TOKEN=your_github_token
```

### Database Setup

The project uses Prisma with SQLite by default. Run these commands from the `apps/frontend-dashboard` directory:

```bash
npx prisma generate
npm run db:push
npx prisma studio
```

## 🎯 Dashboard Modules

### AI Chat
- Real-time conversational AI
- Multiple model support (GPT-4, Claude, Gemini)
- Message history and context management
- Typing indicators and loading states

### Image Generation
- Text-to-image generation
- Multiple size options (256x256, 512x512, 1024x1024)
- Image gallery with download functionality
- Prompt optimization tips

### Web Search
- AI-powered web search
- Result filtering and ranking
- Trending search suggestions
- Search history management

### Code Analysis
- Multi-language code quality analysis and optimization suggestions

### AI Agents
- Agent status monitoring
- Task coordination and tracking
- Performance metrics
- Real-time updates

### Neural Network
- Model training progress
- Performance metrics visualization
- Resource utilization monitoring
- Model management

### GitHub Connect
- Repository management
- Activity tracking
- Automation workflows
- Pull request and issue management

### System Monitor
- Real-time system metrics
- Service health monitoring
- Performance analytics
- Resource utilization

## 🌟 Key Features

### Real-time Communication
- WebSocket integration for live updates
- Socket.IO for scalable real-time features
- Event-driven architecture

### Error Handling
- Comprehensive error boundaries
- Toast notifications for user feedback
- Graceful fallbacks for API failures
- Detailed error logging

### Performance Optimization
- Lazy loading for components
- Optimized bundle sizes
- Efficient state management
- Responsive design patterns

### Data Archive
- **Automatic Archiving**: AI interactions are automatically saved to the archive
- **Manual Archiving**: Save specific interactions manually
- **Search and Filter**: Find specific entries by type or content
- **Export**: Export your archive data as JSON
- **Delete**: Remove individual entries or clear the entire archive

### User Experience
- Intuitive navigation with collapsible sidebar
- Consistent design language
- Accessible components
- Mobile-responsive layouts

## 🔮 AI Integration

The dashboard integrates with the `z-ai-web-dev-sdk` to provide:

### Chat Completions
```javascript
const completion = await zai.chat.completions.create({
  messages: [
    { role: 'system', content: 'You are a helpful assistant.' },
    { role: 'user', content: 'Hello!' }
  ]
})
```

### Image Generation
```javascript
const response = await zai.images.generations.create({
  prompt: 'A beautiful landscape',
  size: '1024x1024'
})
```

### Web Search
```javascript
const results = await zai.functions.invoke('web_search', {
  query: 'Latest AI developments',
  num: 10
})
```

## 🚀 Deployment

### Vercel (Recommended)
1. Connect your GitHub repository to Vercel
2. Configure environment variables
3. Deploy automatically on push

### Docker
```bash
# Build image
docker build -t ai-dashboard .

# Run container
docker run -p 3000:3000 ai-dashboard
```

### Traditional Server
```bash
# Build for production
npm run build

# Start production server
npm start
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Z.ai** - For providing the AI SDK and tools
- **Next.js** - For the amazing React framework
- **shadcn/ui** - For the beautiful component library
- **Tailwind CSS** - For the utility-first CSS framework

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation in the `/docs` folder
- Review the example implementations in `/examples`

---

Built with ❤️ for the AI developer community. Supercharged by [Z.ai](https://chat.z.ai) 🚀