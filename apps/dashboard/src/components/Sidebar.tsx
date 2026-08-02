import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  CreditCard,
  Calendar,
  Settings,
  Moon,
  Sun,
  ChevronLeft,
  ChevronRight,
  Activity,
  Users,
  X
} from 'lucide-react';

interface SidebarProps {
  onToggle?: (isOpen: boolean) => void;
  mobileMenuOpen?: boolean;
  onMobileMenuClose?: () => void;
}

export default function Sidebar({ onToggle, mobileMenuOpen = false, onMobileMenuClose }: SidebarProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [isDark, setIsDark] = useState(() => {
    // Check localStorage or system preference
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [isMobile, setIsMobile] = useState(false);
  const location = useLocation();

  // Check if mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
      if (window.innerWidth < 1024) {
        setIsOpen(false);
      } else {
        setIsOpen(true);
      }
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const toggleSidebar = () => {
    if (isMobile) {
      onMobileMenuClose?.();
    } else {
      const newState = !isOpen;
      setIsOpen(newState);
      onToggle?.(newState);
    }
  };

  const closeMobileSidebar = () => {
    onMobileMenuClose?.();
  };

  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
    document.documentElement.classList.toggle('light', !newTheme);
  };

  const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: Users, label: 'Agents', path: '/agents' },
    { icon: FileText, label: 'Content Queue', path: '/content-queue' },
    { icon: CreditCard, label: 'Payments', path: '/payments' },
    { icon: Calendar, label: 'Calendar', path: '/calendar' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ];

  const isActive = (path: string) => location.pathname === path;

  const sidebarOpen = isMobile ? mobileMenuOpen : isOpen;

  return (
    <>
      {/* Mobile Overlay */}
      {isMobile && sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={closeMobileSidebar}
        />
      )}

      {/* Sidebar */}
      <div 
        className={`fixed left-0 top-0 h-full bg-[#1e1b4b] border-r border-[#3730a3] transition-all duration-300 z-50 ${
          isMobile 
            ? sidebarOpen 
              ? 'w-[290px] translate-x-0' 
              : 'w-[290px] -translate-x-full'
            : isOpen 
              ? 'w-[290px]' 
              : 'w-[80px]'
        }`}
      >
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#3730a3]">
          {isOpen && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-indigo-600 flex items-center justify-center">
                <Activity size={18} className="text-white" />
              </div>
              <span className="font-bold text-lg gradient-text">AIFP-AOS</span>
            </div>
          )}
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg hover:bg-[#3730a3] transition-colors"
          >
            {isMobile ? (
              <X size={20} />
            ) : isOpen ? (
              <ChevronLeft size={20} />
            ) : (
              <ChevronRight size={20} />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              onClick={isMobile ? closeMobileSidebar : undefined}
              className={`flex items-center space-x-3 px-3 py-3 rounded-lg transition-all duration-200 ${
                isActive(item.path)
                  ? 'bg-accent text-white shadow-lg'
                  : 'hover:bg-[#3730a3] text-gray-300 hover:text-white'
              }`}
            >
              <item.icon size={20} />
              {isOpen && <span className="font-medium">{item.label}</span>}
            </Link>
          ))}
        </nav>

        {/* Quick Stats (When Open and Not Mobile) */}
        {isOpen && !isMobile && (
          <div className="px-4 py-4 border-t border-[#3730a3]">
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Active Agents</span>
                <span className="font-semibold text-accent">9</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Campaigns</span>
                <span className="font-semibold text-blue-400">3</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Tasks</span>
                <span className="font-semibold text-green-400">156</span>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="p-4 border-t border-[#3730a3]">
          <div className="flex items-center justify-between">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-[#3730a3] transition-colors"
              title="Toggle Theme"
            >
              {isDark ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            {isOpen && (
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center">
                  <Users size={16} className="text-white" />
                </div>
                <span className="text-sm text-gray-400">Admin</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
