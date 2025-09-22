import React, { useState } from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import {
  BarChart3,
  Search,
  FileText,
  Settings,
  ChevronLeft,
  Activity,
  Database,
  Cog,
  ArrowLeft
} from 'lucide-react';
import RAGDashboard from './RAGDashboard.js';
import RAGSearch from './RAGSearch.js';
import RAGManagement from './RAGManagement.js';
import RAGConfig from './RAGConfig.js';

const RAGRouter = () => {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);
  const navigate = useNavigate();

  const subNavItems = [
    {
      path: '/rag',
      icon: BarChart3,
      label: 'Dashboard',
      description: 'System status & analytics'
    },
    {
      path: '/rag/search',
      icon: Search,
      label: 'Search',
      description: 'Advanced knowledge search'
    },
    {
      path: '/rag/management',
      icon: FileText,
      label: 'Management',
      description: 'Documents & indexes'
    },
    {
      path: '/rag/config',
      icon: Settings,
      label: 'Configuration',
      description: 'Settings & providers'
    },
  ];

  const handleNavigate = (path) => {
    setCurrentPath(path);
    navigate(path);
    window.history.pushState({}, '', path);
  };

  const getCurrentPageTitle = () => {
    const item = subNavItems.find(item => item.path === currentPath);
    return item ? item.label : 'RAG System';
  };

  const getCurrentPageDescription = () => {
    const item = subNavItems.find(item => item.path === currentPath);
    return item ? item.description : 'Retrieval-Augmented Generation System';
  };

  return (
    <div className="w-full h-full bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link
              to="/"
              onClick={(e) => {
                e.preventDefault();
                handleNavigate('/');
              }}
              className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
              title="Back to Home"
            >
              <ArrowLeft className="h-5 w-5" />
              <span className="text-sm">Back</span>
            </Link>
            <div className="h-6 w-px bg-gray-600"></div>
            <div className="flex items-center space-x-3">
              <Activity className="h-6 w-6 text-blue-400" />
              <div>
                <h1 className="text-xl font-semibold">RAG System</h1>
                <p className="text-sm text-gray-400">{getCurrentPageDescription()}</p>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-sm text-gray-400">
              {getCurrentPageTitle()}
            </div>
          </div>
        </div>
      </div>

      <div className="flex h-full">
        {/* Sub-navigation Sidebar */}
        <div className="w-64 bg-gray-800 border-r border-gray-700 p-4">
          <div className="space-y-2">
            {subNavItems.map(item => {
              const Icon = item.icon;
              const isActive = currentPath === item.path;

              return (
                <button
                  key={item.path}
                  onClick={() => handleNavigate(item.path)}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors text-left ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                  title={`${item.label} - ${item.description}`}
                >
                  <Icon className="h-5 w-5" />
                  <div className="flex-1">
                    <div className="font-medium">{item.label}</div>
                    <div className="text-xs opacity-75">{item.description}</div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Quick Stats */}
          <div className="mt-8 p-4 bg-gray-900 rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400 mb-3">Quick Info</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-400">Documents</span>
                <span className="text-white">0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Indexes</span>
                <span className="text-white">0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Searches</span>
                <span className="text-white">0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Status</span>
                <span className="text-yellow-400">Initializing</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<RAGDashboard />} />
            <Route path="/search" element={<RAGSearch />} />
            <Route path="/management" element={<RAGManagement />} />
            <Route path="/config" element={<RAGConfig />} />
          </Routes>
        </div>
      </div>
    </div>
  );
};

export default RAGRouter;