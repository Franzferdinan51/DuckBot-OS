import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Upload,
  Download,
  Code,
  Play,
  Pause,
  X,
  CheckCircle,
  AlertCircle,
  Clock,
  Settings,
  Eye,
  Copy,
  Save,
  FileDown,
  FileUp,
  BookOpen,
  GitBranch,
  TestTube,
  MessageSquare
} from 'lucide-react';

// Paper2Code Component
const DeepCodePaper2Code = ({ onClose }) => {
  // Form state
  const [inputMethod, setInputMethod] = useState('text'); // 'text' or 'upload'
  const [documentText, setDocumentText] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);
  const [generatedCode, setGeneratedCode] = useState(null);
  const [showCodePreview, setShowCodePreview] = useState(false);
  const [config, setConfig] = useState({
    codeStyle: 'modern',
    language: 'python',
    includeComments: true,
    includeTests: true,
    generateReadme: true,
    createGitRepo: false,
  });

  // Mock processing states
  const [processingSteps, setProcessingSteps] = useState([
    { id: 1, name: 'Document Analysis', status: 'pending', description: 'Analyzing document structure and content' },
    { id: 2, name: 'Code Generation', status: 'pending', description: 'Generating source code from document' },
    { id: 3, name: 'Code Review', status: 'pending', description: 'Reviewing and optimizing generated code' },
    { id: 4, name: 'Test Generation', status: 'pending', description: 'Creating unit tests for generated code' },
    { id: 5, name: 'Documentation', status: 'pending', description: 'Generating documentation and README' },
  ]);

  // Language options
  const languageOptions = [
    { value: 'python', label: 'Python', icon: '🐍' },
    { value: 'javascript', label: 'JavaScript', icon: '🟨' },
    { value: 'typescript', label: 'TypeScript', icon: '🔷' },
    { value: 'java', label: 'Java', icon: '☕' },
    { value: 'cpp', label: 'C++', icon: '⚡' },
  ];

  // Code style options
  const styleOptions = [
    { value: 'modern', label: 'Modern', description: 'Clean, modern coding style' },
    { value: 'classic', label: 'Classic', description: 'Traditional, robust coding style' },
    { value: 'minimal', label: 'Minimal', description: 'Minimalist, efficient coding style' },
  ];

  // Handle file upload
  const handleFileUpload = useCallback((event) => {
    const file = event.target.files[0];
    if (file) {
      setUploadedFile(file);
      setInputMethod('upload');

      // For demo purposes, extract text from file
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target.result;
        setDocumentText(text.substring(0, 5000) + '...'); // Limit text for demo
      };
      reader.readAsText(file);
    }
  }, []);

  // Handle drag and drop
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.currentTarget.classList.add('border-purple-500', 'bg-purple-500/10');
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('border-purple-500', 'bg-purple-500/10');
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('border-purple-500', 'bg-purple-500/10');

    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'text/plain' || file.type === 'application/pdf' || file.name.endsWith('.txt') || file.name.endsWith('.pdf'))) {
      setUploadedFile(file);
      setInputMethod('upload');

      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target.result;
        setDocumentText(text.substring(0, 5000) + '...');
      };
      reader.readAsText(file);
    }
  }, []);

  // Start processing
  const startProcessing = useCallback(async () => {
    if (!documentText.trim()) {
      alert('Please provide document text or upload a file');
      return;
    }

    setIsProcessing(true);
    setCurrentJob({
      id: `job_${Date.now()}`,
      type: 'paper2code',
      status: 'processing',
      progress: 0,
      created_at: new Date().toISOString(),
    });

    // Simulate processing steps
    for (let i = 0; i < processingSteps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 2000));

      setProcessingSteps(prev => prev.map(step =>
        step.id === i + 1
          ? { ...step, status: 'processing' }
          : step.id === i
            ? { ...step, status: 'completed' }
            : step
      ));

      setCurrentJob(prev => ({ ...prev, progress: ((i + 1) / processingSteps.length) * 100 }));
    }

    // Complete all steps
    setProcessingSteps(prev => prev.map(step => ({ ...step, status: 'completed' })));
    setCurrentJob(prev => ({ ...prev, status: 'completed', progress: 100 }));

    // Generate mock code output
    const mockCode = {
      files: [
        {
          name: 'main.py',
          content: `# Generated by DeepCode Paper2Code
# Based on research document analysis

def main():
    """
    Main function implementing the core algorithm from the research paper
    """
    print("Paper2Code implementation started")

    # Core algorithm implementation
    result = process_data()
    return result

def process_data():
    """
    Process data according to the research methodology
    """
    # Implementation details from paper
    data = load_data()
    processed = apply_algorithm(data)
    return processed

def load_data():
    """Load and preprocess input data"""
    return []

def apply_algorithm(data):
    """Apply the main algorithm from the research paper"""
    return data

if __name__ == "__main__":
    main()`
        },
        {
          name: 'test_main.py',
          content: `import unittest
from main import process_data, load_data, apply_algorithm

class TestPaper2Code(unittest.TestCase):
    def test_load_data(self):
        """Test data loading functionality"""
        result = load_data()
        self.assertIsInstance(result, list)

    def test_process_data(self):
        """Test main processing function"""
        result = process_data()
        self.assertIsNotNone(result)

    def test_apply_algorithm(self):
        """Test algorithm application"""
        test_data = [1, 2, 3]
        result = apply_algorithm(test_data)
        self.assertEqual(result, test_data)

if __name__ == '__main__':
    unittest.main()`
        },
        {
          name: 'README.md',
          content: `# Paper2Code Generated Project

This project was automatically generated by DeepCode's Paper2Code feature from a research paper.

## Features

- Core algorithm implementation
- Unit tests
- Documentation
- Modern code structure

## Installation

\`\`\`bash
pip install -r requirements.txt
\`\`\`

## Usage

\`\`\`bash
python main.py
\`\`\`

## Running Tests

\`\`\`bash
python test_main.py
\`\`\`

## Generated From

Research paper processed with DeepCode Paper2Code
Configuration: ${config.codeStyle} style, ${config.language} language`
        },
      ],
      metadata: {
        generated_at: new Date().toISOString(),
        paper_length: documentText.length,
        config: config,
        total_files: 3,
      },
    };

    setGeneratedCode(mockCode);
    setIsProcessing(false);
  }, [documentText, config, processingSteps]);

  // Download generated code
  const downloadCode = useCallback(() => {
    if (!generatedCode) return;

    const zipContent = generatedCode.files.map(file =>
      `File: ${file.name}\n\n${file.content}\n${'='.repeat(50)}\n`
    ).join('\n');

    const blob = new Blob([zipContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `paper2code_output_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [generatedCode]);

  // Reset form
  const resetForm = useCallback(() => {
    setDocumentText('');
    setUploadedFile(null);
    setInputMethod('text');
    setGeneratedCode(null);
    setCurrentJob(null);
    setShowCodePreview(false);
    setProcessingSteps(prev => prev.map(step => ({ ...step, status: 'pending' })));
  }, []);

  // Copy code to clipboard
  const copyToClipboard = useCallback((code) => {
    navigator.clipboard.writeText(code);
    // Show success feedback
  }, []);

  return (
    <div className="h-full bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <FileText className="w-6 h-6 text-purple-400" />
            <h2 className="text-white text-xl font-semibold">Paper2Code</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* Input Section */}
          {!currentJob && !generatedCode && (
            <div className="space-y-4">
              <h3 className="text-white text-lg font-medium">Input Document</h3>

              {/* Input Method Selection */}
              <div className="flex space-x-4">
                <button
                  onClick={() => setInputMethod('text')}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    inputMethod === 'text'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <MessageSquare className="w-4 h-4 inline mr-2" />
                  Text Input
                </button>
                <button
                  onClick={() => setInputMethod('upload')}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    inputMethod === 'upload'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <FileUp className="w-4 h-4 inline mr-2" />
                  Upload File
                </button>
              </div>

              {/* Text Input */}
              {inputMethod === 'text' && (
                <div className="space-y-3">
                  <label className="block text-gray-300 text-sm">Document Text</label>
                  <textarea
                    value={documentText}
                    onChange={(e) => setDocumentText(e.target.value)}
                    placeholder="Paste your research paper text here..."
                    className="w-full h-64 bg-gray-800 text-white rounded-lg border border-gray-600 px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              )}

              {/* File Upload */}
              {inputMethod === 'upload' && (
                <div className="space-y-3">
                  <label className="block text-gray-300 text-sm">Upload Document</label>
                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center hover:border-purple-500 transition-colors cursor-pointer"
                    onClick={() => document.getElementById('file-input').click()}
                  >
                    <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-300 mb-2">Drop your document here or click to browse</p>
                    <p className="text-gray-500 text-sm">Supports .txt, .pdf files</p>
                    <input
                      id="file-input"
                      type="file"
                      accept=".txt,.pdf"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                  </div>

                  {uploadedFile && (
                    <div className="bg-gray-800 rounded-lg p-3 flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <FileText className="w-5 h-5 text-purple-400" />
                        <div>
                          <div className="text-white font-medium">{uploadedFile.name}</div>
                          <div className="text-gray-400 text-sm">{(uploadedFile.size / 1024).toFixed(1)} KB</div>
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          setUploadedFile(null);
                          setDocumentText('');
                        }}
                        className="text-gray-400 hover:text-red-400 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Configuration */}
              <div className="bg-gray-800 rounded-lg p-4 space-y-4">
                <h4 className="text-white font-medium">Configuration</h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-gray-300 text-sm mb-2">Language</label>
                    <select
                      value={config.language}
                      onChange={(e) => setConfig(prev => ({ ...prev, language: e.target.value }))}
                      className="w-full bg-gray-700 text-white rounded-lg border border-gray-600 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      {languageOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.icon} {option.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-gray-300 text-sm mb-2">Code Style</label>
                    <select
                      value={config.codeStyle}
                      onChange={(e) => setConfig(prev => ({ ...prev, codeStyle: e.target.value }))}
                      className="w-full bg-gray-700 text-white rounded-lg border border-gray-600 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      {styleOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={config.includeComments}
                      onChange={(e) => setConfig(prev => ({ ...prev, includeComments: e.target.checked }))}
                      className="rounded w-4 h-4 text-purple-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Include Comments</span>
                  </label>

                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={config.includeTests}
                      onChange={(e) => setConfig(prev => ({ ...prev, includeTests: e.target.checked }))}
                      className="rounded w-4 h-4 text-purple-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Generate Tests</span>
                  </label>

                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={config.generateReadme}
                      onChange={(e) => setConfig(prev => ({ ...prev, generateReadme: e.target.checked }))}
                      className="rounded w-4 h-4 text-purple-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Generate README</span>
                  </label>

                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={config.createGitRepo}
                      onChange={(e) => setConfig(prev => ({ ...prev, createGitRepo: e.target.checked }))}
                      className="rounded w-4 h-4 text-purple-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Initialize Git Repository</span>
                  </label>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3">
                <button
                  onClick={resetForm}
                  className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
                >
                  Reset
                </button>
                <button
                  onClick={startProcessing}
                  disabled={isProcessing || !documentText.trim()}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  <Play className="w-4 h-4" />
                  <span>{isProcessing ? 'Processing...' : 'Generate Code'}</span>
                </button>
              </div>
            </div>
          )}

          {/* Processing Section */}
          {currentJob && isProcessing && (
            <div className="space-y-4">
              <h3 className="text-white text-lg font-medium">Processing Document</h3>

              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-gray-300">Progress</span>
                  <span className="text-white font-medium">{currentJob.progress}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-purple-500 h-2 rounded-full transition-all duration-300"
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

          {/* Results Section */}
          {generatedCode && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-white text-lg font-medium">Generated Code</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setShowCodePreview(!showCodePreview)}
                    className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm"
                  >
                    <Eye className="w-4 h-4 inline mr-1" />
                    {showCodePreview ? 'Hide' : 'Show'} Preview
                  </button>
                  <button
                    onClick={downloadCode}
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

              <div className="bg-gray-800 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {generatedCode.files.map((file, index) => (
                    <div key={index} className="bg-gray-700 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-white font-medium">{file.name}</span>
                        <button
                          onClick={() => copyToClipboard(file.content)}
                          className="text-gray-400 hover:text-white transition-colors"
                          title="Copy to clipboard"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="text-gray-400 text-sm mb-2">
                        {file.content.split('\n').length} lines
                      </div>
                      <pre className="text-gray-300 text-xs bg-gray-800 p-2 rounded overflow-x-auto max-h-32">
                        {file.content.substring(0, 200)}...
                      </pre>
                    </div>
                  ))}
                </div>
              </div>

              {showCodePreview && (
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-white font-medium">Full Code Preview</h4>
                    <select className="bg-gray-700 text-white rounded px-2 py-1 text-sm">
                      {generatedCode.files.map((file, index) => (
                        <option key={index} value={index}>{file.name}</option>
                      ))}
                    </select>
                  </div>
                  <pre className="text-gray-300 text-sm bg-gray-900 p-4 rounded overflow-x-auto max-h-96">
                    {generatedCode.files[0]?.content || 'No code available'}
                  </pre>
                </div>
              )}

              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-white font-medium mb-3">Generation Summary</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-purple-400">{generatedCode.metadata.total_files}</div>
                    <div className="text-gray-400 text-sm">Files Generated</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-blue-400">{generatedCode.files.reduce((acc, file) => acc + file.content.split('\n').length, 0)}</div>
                    <div className="text-gray-400 text-sm">Lines of Code</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-400">{config.language}</div>
                    <div className="text-gray-400 text-sm">Language</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-yellow-400">{config.codeStyle}</div>
                    <div className="text-gray-400 text-sm">Code Style</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DeepCodePaper2Code;