import React, { useState } from 'react';

// Inlined SVGs for icons to avoid creating new files
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

interface ChatUIProps {
    onSend: (message: string) => void;
    isLoading: boolean;
    onMicClick: () => void;
    isListening: boolean;
    onSettingsClick: () => void;
}

export const ChatUI: React.FC<ChatUIProps> = ({ onSend, isLoading, onMicClick, isListening, onSettingsClick }) => {
    const [inputValue, setInputValue] = useState('');

    const handleSendClick = () => {
        if (inputValue.trim() && !isLoading) {
            onSend(inputValue.trim());
            setInputValue('');
        }
    };

    const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === 'Enter') {
            handleSendClick();
        }
    };

    return (
        <div className="max-w-2xl mx-auto">
            <div className="flex items-center bg-gray-700 rounded-full shadow-lg p-2 gap-2">
                 <button 
                    onClick={onSettingsClick}
                    className="p-2 hover:bg-gray-600 rounded-full transition-colors"
                    aria-label="Settings"
                >
                    <SettingsIcon />
                </button>
                <input
                    type="text"
                    id="text-input"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={isLoading ? "Thinking..." : (isListening ? "Listening..." : "Ask me anything...")}
                    className="flex-grow bg-transparent text-white placeholder-gray-400 focus:outline-none px-4 py-2"
                    disabled={isLoading || isListening}
                />
                 <button
                    onClick={onMicClick}
                    disabled={isLoading}
                    className="p-2 hover:bg-gray-600 rounded-full transition-colors disabled:opacity-50"
                    aria-label="Use Microphone"
                >
                    <MicIcon isListening={isListening} />
                </button>
                <button
                    id="submit-btn"
                    onClick={handleSendClick}
                    disabled={isLoading || !inputValue.trim()}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-500 disabled:cursor-not-allowed text-white font-bold py-2 px-6 rounded-full transition-colors duration-300 flex items-center justify-center"
                >
                    {isLoading ? <SpinnerIcon /> : 'Send'}
                </button>
            </div>
        </div>
    );
};
