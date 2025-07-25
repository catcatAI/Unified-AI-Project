import "./index.css"
import { HashRouter as Router, Routes, Route } from "react-router-dom"
import { ThemeProvider } from "./components/ui/theme-provider"
import { Toaster } from "./components/ui/toaster"
import { AuthProvider } from "./contexts/AuthContext"
import { Login } from "./pages/Login"
import { Register } from "./pages/Register"
import { ProtectedRoute } from "./components/ProtectedRoute"
import { Layout } from "./components/Layout"
import { BlankPage } from "./pages/BlankPage"
import { Dashboard } from "./pages/Dashboard"
import { ServiceInterface } from "./pages/ServiceInterface"
import { History } from "./pages/History"
import { Workflows } from "./pages/Workflows"
import { Settings } from "./pages/Settings"
import { CodeAnalysis } from "./pages/CodeAnalysis"
import { Game } from "./pages/Game"
import { Chat } from "./pages/Chat"
import { HSP } from "./pages/HSP"

function App() {
  return (
    <AuthProvider>
      <ThemeProvider defaultTheme="light" storageKey="ui-theme">
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route index element={<Dashboard />} />
              <Route path="chat" element={<Chat />} />
              <Route path="hsp" element={<HSP />} />
              <Route path="game" element={<Game />} />
              <Route path="code-analysis" element={<CodeAnalysis />} />
              <Route path="service/:serviceId" element={<ServiceInterface />} />
              <Route path="history" element={<History />} />
              <Route path="workflows" element={<Workflows />} />
              <Route path="settings" element={<Settings />} />
            </Route>
            <Route path="*" element={<BlankPage />} />
          </Routes>
        </Router>
        <Toaster />
      </ThemeProvider>
    </AuthProvider>
  )
}

export default App
