import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Menu } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import CalendarPage from './pages/Calendar'
import Payments from './pages/Payments'
import Settings from './pages/Settings'
import ContentQueue from './pages/ContentQueue'
import AgentDetails from './pages/AgentDetails'
import Sidebar from './components/Sidebar'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Check if mobile
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 1024;
      setIsMobile(mobile);
      setSidebarOpen(!mobile);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  return (
    <Router>
      <div className="min-h-screen bg-[#1e1b4b]">
        <Sidebar 
          onToggle={setSidebarOpen} 
          mobileMenuOpen={mobileMenuOpen}
          onMobileMenuClose={closeMobileMenu}
        />
        
        {/* Mobile Header */}
        {isMobile && (
          <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-[#1e1b4b] border-b border-[#3730a3] z-30 flex items-center justify-between px-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-indigo-600 flex items-center justify-center">
                <span className="text-white font-bold text-sm">AI</span>
              </div>
              <span className="font-bold text-lg gradient-text">AIFP-AOS</span>
            </div>
            <button
              onClick={toggleMobileMenu}
              className="p-2 rounded-lg hover:bg-[#3730a3] transition-colors"
            >
              <Menu size={24} className="text-white" />
            </button>
          </div>
        )}
        
        <main 
          className={`transition-all duration-300 ${
            isMobile 
              ? 'pt-16' 
              : sidebarOpen 
                ? 'ml-[290px]' 
                : 'ml-[80px]'
          }`}
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/calendar" element={<CalendarPage />} />
            <Route path="/payments" element={<Payments />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/content-queue" element={<ContentQueue />} />
            <Route path="/agent/:agentName" element={<AgentDetails />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
