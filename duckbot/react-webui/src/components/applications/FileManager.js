import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useSystem } from '../../contexts/SystemContext';

const FileManager = () => {
  const [currentPath, setCurrentPath] = useState('/');
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const loadDirectory = async (path) => {
    setLoading(true);
    try {
      // Placeholder for file system integration
      const mockFiles = [
        { name: 'Documents', type: 'folder', size: '-', modified: '2024-01-15' },
        { name: 'duckbot.log', type: 'file', size: '2.4 KB', modified: '2024-01-20' },
        { name: 'config.json', type: 'file', size: '1.2 KB', modified: '2024-01-19' },
        { name: 'assets', type: 'folder', size: '-', modified: '2024-01-18' }
      ];
      setFiles(mockFiles);
    } catch (error) {
      console.error('Error loading directory:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadDirectory(currentPath);
  }, [currentPath]);

  return (
    <div className="file-manager">
      <div className="file-manager-header">
        <div className="path-bar">
          <span>📁 {currentPath}</span>
        </div>
        <div className="file-actions">
          <button className="btn btn-sm">New Folder</button>
          <button className="btn btn-sm">Upload</button>
        </div>
      </div>

      <div className="file-list">
        {loading ? (
          <div className="loading">Loading files...</div>
        ) : (
          files.map((file, index) => (
            <motion.div
              key={file.name}
              className={`file-item ${selectedFile === file.name ? 'selected' : ''}`}
              onClick={() => setSelectedFile(file.name)}
              whileHover={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}
            >
              <span className="file-icon">
                {file.type === 'folder' ? '📁' : '📄'}
              </span>
              <span className="file-name">{file.name}</span>
              <span className="file-size">{file.size}</span>
              <span className="file-modified">{file.modified}</span>
            </motion.div>
          ))
        )}
      </div>

      <style jsx>{`
        .file-manager {
          height: 100%;
          display: flex;
          flex-direction: column;
          background: #1a1a2e;
          color: white;
        }
        .file-manager-header {
          padding: 1rem;
          border-bottom: 1px solid #333;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .path-bar {
          background: #0f0f1a;
          padding: 0.5rem;
          border-radius: 4px;
          font-family: monospace;
        }
        .file-actions {
          display: flex;
          gap: 0.5rem;
        }
        .btn {
          background: #10b981;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.8rem;
        }
        .btn:hover {
          background: #059669;
        }
        .file-list {
          flex: 1;
          overflow-y: auto;
          padding: 1rem;
        }
        .file-item {
          display: grid;
          grid-template-columns: 2rem 1fr auto auto;
          gap: 1rem;
          padding: 0.5rem;
          border-radius: 4px;
          cursor: pointer;
          margin-bottom: 0.25rem;
        }
        .file-item:hover {
          background: rgba(16, 185, 129, 0.1);
        }
        .file-item.selected {
          background: rgba(16, 185, 129, 0.2);
        }
        .file-name {
          font-weight: 500;
        }
        .file-size, .file-modified {
          font-size: 0.8rem;
          color: #888;
        }
        .loading {
          text-align: center;
          padding: 2rem;
          color: #888;
        }
      `}</style>
    </div>
  );
};

export default FileManager;