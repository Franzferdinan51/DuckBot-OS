import React, { useState } from 'react';

// Inlined SVGs for icons with DuckBot branding
const SpinnerIcon: React.FC = () => (
    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
);

const MicIcon: React.FC<{ isListening: boolean }> = ({ isListening }) => (
    <svg className={`h-6 w-6 transition-colors ${isListening ? 'text-red-500 animate-pulse' : 'text-white'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
    </svg>
);

const SettingsIcon: React.FC = () => (
    <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
);

const DuckBotIcon: React.FC = () => (
    <svg className="h-5 w-5 text-teal-400" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
    </svg>
);

const MinimizeIcon: React.FC = () => (
    <svg className="h-4 w-4 text-gray-400 hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 12H4" />
    </svg>
);

interface ChatUIProps {
    onSend: (message: string) => void;
    isLoading: boolean;
    onMicClick: () => void;
    isListening: boolean;
    onSettingsClick: () => void;
    onMinimizeClick?: () => void;
    connectionStatus?: 'connected' | 'connecting' | 'disconnected';
    currentProvider?: string;
}

export const ChatUI: React.FC<ChatUIProps> = ({ 
    onSend, 
    isLoading, 
    onMicClick, 
    isListening, 
    onSettingsClick, 
    onMinimizeClick,
    connectionStatus = 'disconnected',
    currentProvider = 'duckbot'
}) => {
    const [inputValue, setInputValue] = useState('');

    const handleSendClick = () => {
        if (inputValue.trim() && !isLoading && connectionStatus === 'connected') {
            onSend(inputValue.trim());
            setInputValue('');
        }
    };

    const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === 'Enter') {
            handleSendClick();
        }
    };

    const getStatusColor = () => {
        switch (connectionStatus) {
            case 'connected': return 'text-green-400';
            case 'connecting': return 'text-yellow-400';
            case 'disconnected': return 'text-red-400';
            default: return 'text-gray-400';
        }
    };

    const getStatusText = () => {
        switch (connectionStatus) {
            case 'connected': return `Connected to ${currentProvider.toUpperCase()}`;
            case 'connecting': return 'Connecting...';
            case 'disconnected': return 'Disconnected';
            default: return 'Unknown status';
        }
    };

    const getPlaceholder = () => {
        if (connectionStatus === 'disconnected') return 'Connect to DuckBot first...';
        if (connectionStatus === 'connecting') return 'Connecting...';
        if (isLoading) return 'Thinking...';
        if (isListening) return 'Listening...';
        return 'Ask your DuckBot Clippy anything...';
    };

    return (
        <div className="w-full">
            {/* Header with status and controls */}
            <div className="flex items-center justify-between px-4 py-2 bg-gray-800 rounded-t-lg">
                <div className="flex items-center gap-2">
                    <DuckBotIcon />
                    <span className="text-sm font-medium text-white">DuckBot Clippy</span>
                    <div className={`text-xs ${getStatusColor()}`}>
                        {getStatusText()}
                    </div>
                </div>
                {onMinimizeClick && (
                    <button 
                        onClick={onMinimizeClick}
                        className="p-1 hover:bg-gray-700 rounded transition-colors"
                        aria-label="Minimize to tray"
                    >
                        <MinimizeIcon />
                    </button>
                )}
            </div>

            {/* Main chat interface */}
            <div className="bg-gray-700 rounded-b-lg p-3">
                <div className="flex items-center gap-2">
                    <button 
                        onClick={onSettingsClick}
                        className="p-2 hover:bg-gray-600 rounded-full transition-colors flex-shrink-0"
                        aria-label="Settings"
                    >
                        <SettingsIcon />
                    </button>
                    
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder={getPlaceholder()}
                        className="flex-grow bg-gray-600 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-400 px-4 py-2 rounded-full"
                        disabled={isLoading || isListening || connectionStatus !== 'connected'}
                    />
                    
                    <button
                        onClick={onMicClick}
                        disabled={isLoading || connectionStatus !== 'connected'}
                        className="p-2 hover:bg-gray-600 rounded-full transition-colors disabled:opacity-50 flex-shrink-0"
                        aria-label="Use Microphone"
                    >
                        <MicIcon isListening={isListening} />
                    </button>
                    
                    <button
                        onClick={handleSendClick}
                        disabled={isLoading || !inputValue.trim() || connectionStatus !== 'connected'}
                        className="bg-teal-600 hover:bg-teal-700 disabled:bg-gray-500 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-full transition-colors duration-200 flex items-center justify-center min-w-[70px] flex-shrink-0"
                    >
                        {isLoading ? <SpinnerIcon /> : 'Send'}
                    </button>
                </div>

                {/* Quick action buttons */}
                <div className="grid grid-cols-3 gap-2 mt-2">
                    <button 
                        onClick={() => onSend("Hello! What can you help me with?")}
                        disabled={isLoading || connectionStatus !== 'connected'}
                        className="text-xs bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 text-gray-200 px-3 py-1 rounded-full transition-colors"
                    >
                        Hello
                    </button>
                    <button 
                        onClick={() => onSend("What's my system status?")}
                        disabled={isLoading || connectionStatus !== 'connected'}
                        className="text-xs bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 text-gray-200 px-3 py-1 rounded-full transition-colors"
                    >
                        System Status
                    </button>
                    <button 
                        onClick={() => onSend("Help me with coding")}
                        disabled={isLoading || connectionStatus !== 'connected'}
                        className="text-xs bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 text-gray-200 px-3 py-1 rounded-full transition-colors"
                    >
                        Code Help
                    </button>
                    <button 
                        onClick={() => onSend("Generate an image of a futuristic robot")}
                        disabled={isLoading || connectionStatus !== 'connected'}
                        className="text-xs bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 text-gray-200 px-3 py-1 rounded-full transition-colors"
                    >
                        🎨 Image Gen
                    </button>
                    <button 
                        onClick={() => onSend("Show my cost summary")}
                        disabled={isLoading || connectionStatus !== 'connected'}
                        className="text-xs bg-green-600 hover:bg-green-500 disabled:bg-gray-700 text-gray-200 px-3 py-1 rounded-full transition-colors"
                    >
                        💰 Costs
                    </button>
                    <button 
                        onClick={() => onSend("Show services status")}
                        disabled={isLoading || connectionStatus !== 'connected'}
                        className="text-xs bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 text-gray-200 px-3 py-1 rounded-full transition-colors"
                    >
                        🔧 Services
                    </button>
                    <button 
                        onClick={() => onSend("Show n8n workflows")}
                        disabled={isLoading || connectionStatus !== 'connected'}
                        className="text-xs bg-orange-600 hover:bg-orange-500 disabled:bg-gray-700 text-gray-200 px-3 py-1 rounded-full transition-colors"
                    >
                        🔄 Workflows
                    </button>
                    <button 
                        onClick={() => onSend("Show queue status")}
                        disabled={isLoading || connectionStatus !== 'connected'}
                        className="text-xs bg-yellow-600 hover:bg-yellow-500 disabled:bg-gray-700 text-gray-200 px-3 py-1 rounded-full transition-colors"
                    >
                        📋 Queue
                    </button>
                </div>
            </div>
        </div>
    );
};