import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Globe,
  Code,
  Palette,
  Layout,
  Database,
  Users,
  ShoppingBag,
  FileText,
  FolderTree, // Using FolderTree instead of non-existent FileTree
  Play,
  Pause,
  X,
  CheckCircle,
  AlertCircle,
  Clock,
  Settings,
  Eye,
  Copy,
  Download,
  Folder,
  Smartphone,
  Monitor,
  Tablet,
  Zap,
  Layers,
  GitBranch,
  ExternalLink,
  FolderOpen
} from 'lucide-react';

// Text2Web Component
const DeepCodeText2Web = ({ onClose }) => {
  // Form state
  const [step, setStep] = useState(1); // 1: Description, 2: Configuration, 3: Generation, 4: Results
  const [projectDescription, setProjectDescription] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);
  const [generatedProject, setGeneratedProject] = useState(null);
  const [showCodePreview, setShowCodePreview] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  // Configuration state
  const [config, setConfig] = useState({
    framework: 'react',
    styling: 'tailwind',
    features: [],
    pages: ['home'],
    projectName: 'my-web-app',
    includeTests: true,
    includeDocumentation: true,
    responsiveDesign: true,
    pwa: false,
    gitRepo: false,
  });

  // Predefined features
  const availableFeatures = [
    { id: 'authentication', label: 'User Authentication', icon: Users, description: 'Login, registration, user management' },
    { id: 'database', label: 'Database Integration', icon: Database, description: 'Database connection and models' },
    { id: 'api', label: 'REST API', icon: ExternalLink, description: 'RESTful API endpoints' },
    { id: 'forms', label: 'Forms & Validation', icon: FolderTree, description: 'Form handling and validation' },
    { id: 'dashboard', label: 'Admin Dashboard', icon: Layout, description: 'Admin interface and analytics' },
    { id: 'ecommerce', label: 'E-commerce', icon: ShoppingBag, description: 'Shopping cart, checkout, payments' },
    { id: 'blog', label: 'Blog System', icon: FileText, description: 'Blog posts, categories, comments' },
    { id: 'search', label: 'Search Functionality', icon: Zap, description: 'Search and filtering' },
    { id: 'notifications', label: 'Notifications', icon: AlertCircle, description: 'Email and in-app notifications' },
    { id: 'fileUpload', label: 'File Upload', icon: FolderOpen, description: 'File upload and management' },
  ];

  // Framework options
  const frameworkOptions = [
    { value: 'react', label: 'React', icon: '⚛️', description: 'Modern React with hooks' },
    { value: 'vue', label: 'Vue.js', icon: '💚', description: 'Progressive Vue.js framework' },
    { value: 'angular', label: 'Angular', icon: '🅰️', description: 'Full-featured Angular framework' },
    { value: 'svelte', label: 'Svelte', icon: '🔥', description: 'Compile-time optimized Svelte' },
  ];

  // Styling options
  const stylingOptions = [
    { value: 'tailwind', label: 'Tailwind CSS', icon: '🎨', description: 'Utility-first CSS framework' },
    { value: 'css', label: 'Plain CSS', icon: '📝', description: 'Standard CSS with custom styling' },
    { value: 'styled-components', label: 'Styled Components', icon: '💎', description: 'CSS-in-JS styled components' },
    { value: 'bootstrap', label: 'Bootstrap', icon: '🅱️', description: 'Popular Bootstrap framework' },
  ];

  // Page templates
  const pageTemplates = [
    { id: 'home', label: 'Home Page', description: 'Landing page with hero section' },
    { id: 'about', label: 'About Page', description: 'Company/team information' },
    { id: 'contact', label: 'Contact Page', description: 'Contact form and information' },
    { id: 'services', label: 'Services Page', description: 'Services overview' },
    { id: 'portfolio', label: 'Portfolio', description: 'Project showcase' },
    { id: 'blog', label: 'FileText List', description: 'FileText posts listing' },
    { id: 'dashboard', label: 'Dashboard', description: 'Admin dashboard' },
    { id: 'profile', label: 'User Profile', description: 'User profile management' },
  ];

  // Processing steps
  const [processingSteps, setProcessingSteps] = useState([
    { id: 1, name: 'Requirements Analysis', status: 'pending', description: 'Analyzing project requirements' },
    { id: 2, name: 'Architecture Design', status: 'pending', description: 'Designing application architecture' },
    { id: 3, name: 'Component Generation', status: 'pending', description: 'Generating React components' },
    { id: 4, name: 'Styling Implementation', status: 'pending', description: 'Applying styles and themes' },
    { id: 5, name: 'Feature Integration', status: 'pending', description: 'Integrating selected features' },
    { id: 6, name: 'Testing Setup', status: 'pending', description: 'Setting up testing framework' },
  ]);

  // Handle feature toggle
  const toggleFeature = useCallback((featureId) => {
    setConfig(prev => ({
      ...prev,
      features: prev.features.includes(featureId)
        ? prev.features.filter(f => f !== featureId)
        : [...prev.features, featureId]
    }));
  }, []);

  // Handle page toggle
  const togglePage = useCallback((pageId) => {
    setConfig(prev => ({
      ...prev,
      pages: prev.pages.includes(pageId)
        ? prev.pages.filter(p => p !== pageId)
        : [...prev.pages, pageId]
    }));
  }, []);

  // Generate project
  const generateProject = useCallback(async () => {
    if (!projectDescription.trim()) {
      alert('Please provide a project description');
      return;
    }

    setIsProcessing(true);
    setCurrentJob({
      id: `job_${Date.now()}`,
      type: 'text2web',
      status: 'processing',
      progress: 0,
      created_at: new Date().toISOString(),
    });

    // Simulate processing
    for (let i = 0; i < processingSteps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 2000));

      processingSteps[i].status = 'processing';
      if (i > 0) processingSteps[i - 1].status = 'completed';

      setProcessingSteps([...processingSteps]);
      setCurrentJob(prev => ({ ...prev, progress: ((i + 1) / processingSteps.length) * 100 }));
    }

    processingSteps[processingSteps.length - 1].status = 'completed';
    setProcessingSteps([...processingSteps]);
    setCurrentJob(prev => ({ ...prev, status: 'completed', progress: 100 }));

    // Generate mock project structure
    const mockProject = {
      name: config.projectName,
      framework: config.framework,
      structure: {
        'src/': {
          'components/': generateComponents(),
          'pages/': generatePages(),
          'styles/': {
            'globals.css': '/* Global styles */',
            [`${config.styling}.config.js`]: generateStylingConfig(),
          },
          'utils/': {
            'helpers.js': '// Utility functions',
          },
          'App.js': generateAppComponent(),
          'index.js': generateIndexFile(),
        },
        'public/': {
          'index.html': generateIndexHtml(),
          'favicon.ico': '',
        },
        'package.json': generatePackageJson(),
        'README.md': generateReadme(),
      },
      features: config.features,
      pages: config.pages,
    };

    setGeneratedProject(mockProject);
    setIsProcessing(false);
  }, [projectDescription, config, processingSteps]);

  // Helper functions for generating content
  const generateComponents = () => {
    const components = {};

    // Basic components
    components['Header.js'] = `import React from 'react';

const Header = () => {
  return (
    <header className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-gray-900">${config.projectName}</h1>
            </div>
            <nav className="ml-6 flex space-x-8">
              ${config.pages.map(page => `
              <a href="/${page}" className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                ${page.charAt(0).toUpperCase() + page.slice(1)}
              </a>`).join('')}
            </nav>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;`;

    components['Footer.js'] = `import React from 'react';

const Footer = () => {
  return (
    <footer className="bg-gray-800 text-white">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <p>&copy; 2024 ${config.projectName}. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;`;

    if (config.features.includes('authentication')) {
      components['Auth.js'] = `// Authentication components`;
    }

    if (config.features.includes('forms')) {
      components['Form.js'] = `// Form components`;
    }

    return components;
  };

  const generatePages = () => {
    const pages = {};

    config.pages.forEach(page => {
      pages[`${page.charAt(0).toUpperCase() + page.slice(1)}.js`] = `import React from 'react';

const ${page.charAt(0).toUpperCase() + page.slice(1)} = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg p-4">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">${page.charAt(0).toUpperCase() + page.slice(1)} Page</h1>
            <p className="text-gray-600">This is the ${page} page of ${config.projectName}.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ${page.charAt(0).toUpperCase() + page.slice(1)};`;
    });

    return pages;
  };

  const generateAppComponent = () => {
    const imports = config.pages.map(page =>
      `import ${page.charAt(0).toUpperCase() + page.slice(1)} from './pages/${page.charAt(0).toUpperCase() + page.slice(1)}';`
    ).join('\n');

    return `import React from 'react';
${imports}
import Header from './components/Header';
import Footer from './components/Footer';

function App() {
  return (
    <div className="App">
      <Header />
      <main>
        {/* Add routing here based on your needs */}
        <${config.pages[0] ? config.pages[0].charAt(0).toUpperCase() + config.pages[0].slice(1) : 'Home'} />
      </main>
      <Footer />
    </div>
  );
}

export default App;`;
  };

  const generateIndexFile = () => `import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/globals.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);`;

  const generateIndexHtml = () => `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="${config.projectName} - ${projectDescription}" />
    <title>${config.projectName}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>`;

  const generatePackageJson = () => ({
    name: config.projectName,
    version: "1.0.0",
    description: projectDescription,
    main: "src/index.js",
    scripts: {
      start: "react-scripts start",
      build: "react-scripts build",
      test: "react-scripts test",
      eject: "react-scripts eject"
    },
    dependencies: {
      "react": "^18.2.0",
      "react-dom": "^18.2.0",
      "react-scripts": "5.0.1",
      ...(config.styling === 'tailwind' ? { "tailwindcss": "^3.3.0" } : {}),
      ...(config.styling === 'styled-components' ? { "styled-components": "^5.3.0" } : {}),
      ...(config.styling === 'bootstrap' ? { "bootstrap": "^5.3.0" } : {}),
    },
    devDependencies: {
      ...(config.includeTests ? { "@testing-library/jest-dom": "^5.16.4" } : {}),
      ...(config.includeTests ? { "@testing-library/react": "^13.3.0" } : {}),
    },
    browserslist: {
      production: [">0.2%", "not dead", "not op_mini all"],
      development: ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
    }
  });

  const generateStylingConfig = () => {
    if (config.styling === 'tailwind') {
      return `/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}`;
    }
    return '';
  };

  const generateReadme = () => `# ${config.projectName}

${projectDescription}

## Features
${config.features.map(feature => `- ${feature}`).join('\n')}

## Pages
${config.pages.map(page => `- ${page.charAt(0).toUpperCase() + page.slice(1)}`).join('\n')}

## Getting Started

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Clone the repository
\`\`\`bash
git clone <repository-url>
cd ${config.projectName}
\`\`\`

2. Install dependencies
\`\`\`bash
npm install
\`\`\`

3. Start the development server
\`\`\`bash
npm start
\`\`\`

Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

### Build for Production

\`\`\`bash
npm run build
\`\`\`

## Technology Stack
- **Framework**: ${config.framework}
- **Styling**: ${config.styling}
- **Build Tool**: Create React App

## License

MIT`;

  // Download project
  const downloadProject = useCallback(() => {
    if (!generatedProject) return;

    const projectFiles = [];

    const flattenStructure = (structure, path = '') => {
      Object.entries(structure).forEach(([key, value]) => {
        const fullPath = path ? `${path}/${key}` : key;

        if (typeof value === 'object' && !value.toString().includes('exports')) {
          flattenStructure(value, fullPath);
        } else {
          projectFiles.push({ path: fullPath, content: value });
        }
      });
    };

    flattenStructure(generatedProject.structure);

    const zipContent = projectFiles.map(file =>
      `File: ${file.path}\n\n${file.content}\n${'='.repeat(50)}\n`
    ).join('\n');

    const blob = new Blob([zipContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${config.projectName}_webapp_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [generatedProject, config]);

  // Reset form
  const resetForm = useCallback(() => {
    setProjectDescription('');
    setStep(1);
    setGeneratedProject(null);
    setCurrentJob(null);
    setShowCodePreview(false);
    setConfig({
      framework: 'react',
      styling: 'tailwind',
      features: [],
      pages: ['home'],
      projectName: 'my-web-app',
      includeTests: true,
      includeDocumentation: true,
      responsiveDesign: true,
      pwa: false,
      gitRepo: false,
    });
    processingSteps.forEach(step => step.status = 'pending');
  }, []);

  return (
    <div className="h-full bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Globe className="w-6 h-6 text-blue-400" />
            <h2 className="text-white text-xl font-semibold">Text2Web</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="bg-gray-800 px-6 py-4">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          {[1, 2, 3, 4].map((stepNumber) => (
            <div key={stepNumber} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= stepNumber
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-400'
                }`}
              >
                {stepNumber}
              </div>
              <div className={`ml-2 text-sm font-medium ${
                step === stepNumber ? 'text-blue-400' : 'text-gray-400'
              }`}>
                {stepNumber === 1 && 'Description'}
                {stepNumber === 2 && 'Configuration'}
                {stepNumber === 3 && 'Generation'}
                {stepNumber === 4 && 'Results'}
              </div>
              {stepNumber < 4 && (
                <div className={`mx-4 w-16 h-0.5 ${
                  step > stepNumber ? 'bg-blue-600' : 'bg-gray-700'
                }`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Step 1: Description */}
        {step === 1 && (
          <div className="max-w-4xl mx-auto space-y-6">
            <h3 className="text-white text-lg font-medium">Describe Your Web Application</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-gray-300 text-sm mb-2">Project Description</label>
                <textarea
                  value={projectDescription}
                  onChange={(e) => setProjectDescription(e.target.value)}
                  placeholder="Describe your web application in detail. What should it do? Who is it for? What features should it have?"
                  className="w-full h-48 bg-gray-800 text-white rounded-lg border border-gray-600 px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-gray-500 text-sm mt-2">
                  {projectDescription.length}/500 characters
                </p>
              </div>

              <div>
                <label className="block text-gray-300 text-sm mb-2">Project Name</label>
                <input
                  type="text"
                  value={config.projectName}
                  onChange={(e) => setConfig(prev => ({ ...prev, projectName: e.target.value }))}
                  placeholder="my-web-app"
                  className="w-full bg-gray-800 text-white rounded-lg border border-gray-600 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={resetForm}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
              >
                Reset
              </button>
              <button
                onClick={() => setStep(2)}
                disabled={!projectDescription.trim()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Configuration */}
        {step === 2 && (
          <div className="max-w-6xl mx-auto space-y-6">
            <h3 className="text-white text-lg font-medium">Configure Your Web Application</h3>

            {/* Framework Selection */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-4">Framework</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {frameworkOptions.map((framework) => (
                  <button
                    key={framework.value}
                    onClick={() => setConfig(prev => ({ ...prev, framework: framework.value }))}
                    className={`p-4 rounded-lg border-2 transition-colors text-left ${
                      config.framework === framework.value
                        ? 'border-blue-500 bg-blue-500/20'
                        : 'border-gray-600 hover:border-gray-500 hover:bg-gray-700'
                    }`}
                  >
                    <div className="text-2xl mb-2">{framework.icon}</div>
                    <div className="text-white font-medium">{framework.label}</div>
                    <div className="text-gray-400 text-sm">{framework.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Styling Selection */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-4">Styling</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stylingOptions.map((style) => (
                  <button
                    key={style.value}
                    onClick={() => setConfig(prev => ({ ...prev, styling: style.value }))}
                    className={`p-4 rounded-lg border-2 transition-colors text-left ${
                      config.styling === style.value
                        ? 'border-blue-500 bg-blue-500/20'
                        : 'border-gray-600 hover:border-gray-500 hover:bg-gray-700'
                    }`}
                  >
                    <div className="text-2xl mb-2">{style.icon}</div>
                    <div className="text-white font-medium">{style.label}</div>
                    <div className="text-gray-400 text-sm">{style.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Features Selection */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-4">Features</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {availableFeatures.map((feature) => {
                  const Icon = feature.icon;
                  return (
                    <button
                      key={feature.id}
                      onClick={() => toggleFeature(feature.id)}
                      className={`p-4 rounded-lg border-2 transition-colors text-left ${
                        config.features.includes(feature.id)
                          ? 'border-blue-500 bg-blue-500/20'
                          : 'border-gray-600 hover:border-gray-500 hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <Icon className="w-5 h-5 text-blue-400" />
                        <div>
                          <div className="text-white font-medium">{feature.label}</div>
                          <div className="text-gray-400 text-sm">{feature.description}</div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Pages Selection */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-4">Pages</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {pageTemplates.map((page) => (
                  <button
                    key={page.id}
                    onClick={() => togglePage(page.id)}
                    className={`p-3 rounded-lg border-2 transition-colors text-left ${
                      config.pages.includes(page.id)
                        ? 'border-blue-500 bg-blue-500/20'
                        : 'border-gray-600 hover:border-gray-500 hover:bg-gray-700'
                    }`}
                  >
                    <div className="text-white font-medium">{page.label}</div>
                    <div className="text-gray-400 text-sm">{page.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Additional Options */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-4">Additional Options</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={config.includeTests}
                    onChange={(e) => setConfig(prev => ({ ...prev, includeTests: e.target.checked }))}
                    className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300">Include Tests</span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={config.includeDocumentation}
                    onChange={(e) => setConfig(prev => ({ ...prev, includeDocumentation: e.target.checked }))}
                    className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300">Include Documentation</span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={config.responsiveDesign}
                    onChange={(e) => setConfig(prev => ({ ...prev, responsiveDesign: e.target.checked }))}
                    className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300">Responsive Design</span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={config.pwa}
                    onChange={(e) => setConfig(prev => ({ ...prev, pwa: e.target.checked }))}
                    className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300">Progressive Web App</span>
                </label>
              </div>
            </div>

            <div className="flex justify-between space-x-3">
              <button
                onClick={() => setStep(1)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
              >
                Previous
              </button>
              <button
                onClick={() => setStep(3)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Generation */}
        {step === 3 && (
          <div className="max-w-4xl mx-auto space-y-6">
            <h3 className="text-white text-lg font-medium">Generate Your Web Application</h3>

            {!currentJob && !generatedProject && (
              <div className="bg-gray-800 rounded-lg p-6 text-center">
                <Code className="w-16 h-16 text-blue-400 mx-auto mb-4" />
                <h4 className="text-white text-lg font-medium mb-2">Ready to Generate</h4>
                <p className="text-gray-400 mb-6">
                  Based on your description and configuration, we'll generate a complete {config.framework} web application with:
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-400">{config.pages.length}</div>
                    <div className="text-gray-400 text-sm">Pages</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-400">{config.features.length}</div>
                    <div className="text-gray-400 text-sm">Features</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-400">{config.framework}</div>
                    <div className="text-gray-400 text-sm">Framework</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-400">{config.styling}</div>
                    <div className="text-gray-400 text-sm">Styling</div>
                  </div>
                </div>
                <button
                  onClick={generateProject}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium"
                >
                  Generate Web Application
                </button>
              </div>
            )}

            {/* Processing UI */}
            {currentJob && isProcessing && (
              <div className="space-y-4">
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-gray-300">Progress</span>
                    <span className="text-white font-medium">{currentJob.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${currentJob.progress}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  {processingSteps.map((step) => (
                    <div
                      key={step.id}
                      className="flex items-center space-x-3 p-3 bg-gray-800 rounded-lg"
                    >
                      {step.status === 'pending' && <Clock className="w-5 h-5 text-gray-400" />}
                      {step.status === 'processing' && <Play className="w-5 h-5 text-blue-400 animate-pulse" />}
                      {step.status === 'completed' && <CheckCircle className="w-5 h-5 text-green-400" />}
                      <div className="flex-1">
                        <div className="text-white font-medium">{step.name}</div>
                        <div className="text-gray-400 text-sm">{step.description}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {generatedProject && (
              <div className="flex justify-center">
                <button
                  onClick={() => setStep(4)}
                  className="px-6 py-3 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors font-medium"
                >
                  View Generated Project
                </button>
              </div>
            )}
          </div>
        )}

        {/* Step 4: Results */}
        {step === 4 && generatedProject && (
          <div className="max-w-6xl mx-auto space-y-6">
            <h3 className="text-white text-lg font-medium">Generated Web Application</h3>

            {/* Project Summary */}
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-white font-medium">{generatedProject.name}</h4>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setShowCodePreview(!showCodePreview)}
                    className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm"
                  >
                    <Eye className="w-4 h-4 inline mr-1" />
                    {showCodePreview ? 'Hide' : 'Show'} Code
                  </button>
                  <button
                    onClick={downloadProject}
                    className="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors text-sm"
                  >
                    <Download className="w-4 h-4 inline mr-1" />
                    Download
                  </button>
                  <button
                    onClick={resetForm}
                    className="px-3 py-1 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors text-sm"
                  >
                    <Play className="w-4 h-4 inline mr-1" />
                    New Project
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">{generatedProject.pages.length}</div>
                  <div className="text-gray-400 text-sm">Pages</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">{generatedProject.features.length}</div>
                  <div className="text-gray-400 text-sm">Features</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-400">{generatedProject.framework}</div>
                  <div className="text-gray-400 text-sm">Framework</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-400">{Object.keys(generatedProject.structure).length}</div>
                  <div className="text-gray-400 text-sm">Directories</div>
                </div>
              </div>
            </div>

            {/* File Structure */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h4 className="text-white font-medium mb-4">Project Structure</h4>
              <ProjectFolderTree structure={generatedProject.structure} />
            </div>

            {/* Code Preview */}
            {showCodePreview && (
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-white font-medium">Code Preview</h4>
                  <select
                    value={selectedFile || ''}
                    onChange={(e) => setSelectedFile(e.target.value)}
                    className="bg-gray-700 text-white rounded px-2 py-1 text-sm"
                  >
                    <option value="">Select a file to preview</option>
                    {flattenFileList(generatedProject.structure).map(file => (
                      <option key={file.path} value={file.path}>{file.path}</option>
                    ))}
                  </select>
                </div>
                {selectedFile && (
                  <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-gray-300 text-sm">
                      {getFileContent(generatedProject.structure, selectedFile)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// File Tree Component
const ProjectFolderTree = ({ structure, path = '', depth = 0 }) => {
  return (
    <div className={`space-y-1 ${depth > 0 ? 'ml-4' : ''}`}>
      {Object.entries(structure).map(([key, value]) => {
        const fullPath = path ? `${path}/${key}` : key;
        const isDirectory = typeof value === 'object' && !value.toString().includes('exports');

        return (
          <div key={fullPath}>
            <div className="flex items-center space-x-2 text-gray-300">
              {isDirectory ? (
                <FolderOpen className="w-4 h-4 text-yellow-400" />
              ) : (
                <ProjectFolderTreeIcon filename={key} />
              )}
              <span className={isDirectory ? 'font-medium' : ''}>{key}</span>
            </div>
            {isDirectory && (
              <ProjectFolderTree structure={value} path={fullPath} depth={depth + 1} />
            )}
          </div>
        );
      })}
    </div>
  );
};

const ProjectFolderTreeIcon = ({ filename }) => {
  const extension = filename.split('.').pop()?.toLowerCase();

  if (['js', 'jsx', 'ts', 'tsx'].includes(extension)) {
    return <Code className="w-4 h-4 text-blue-400" />;
  } else if (['css', 'scss', 'sass'].includes(extension)) {
    return <Palette className="w-4 h-4 text-pink-400" />;
  } else if (['json'].includes(extension)) {
    return <Database className="w-4 h-4 text-green-400" />;
  } else if (['html'].includes(extension)) {
    return <Globe className="w-4 h-4 text-orange-400" />;
  } else if (['md'].includes(extension)) {
    return <FileText className="w-4 h-4 text-gray-400" />;
  }

  return <FolderTree className="w-4 h-4 text-gray-400" />;
};

// Helper functions
const flattenFileList = (structure, path = '') => {
  let files = [];

  Object.entries(structure).forEach(([key, value]) => {
    const fullPath = path ? `${path}/${key}` : key;

    if (typeof value === 'object' && !value.toString().includes('exports')) {
      files = files.concat(flattenFileList(value, fullPath));
    } else {
      files.push({ path: fullPath, content: value });
    }
  });

  return files;
};

const getFileContent = (structure, filePath) => {
  const parts = filePath.split('/');
  let current = structure;

  for (const part of parts) {
    if (current[part]) {
      current = current[part];
    } else {
      return 'File not found';
    }
  }

  return typeof current === 'string' ? current : JSON.stringify(current, null, 2);
};

export default DeepCodeText2Web;