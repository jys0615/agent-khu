import React from 'react';
import ChatInterface from './components/ChatInterface';

function App() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
            <header className="bg-white shadow-sm">
                <div className="max-w-4xl mx-auto px-4 py-4">
                    <h1 className="text-2xl font-bold text-gray-800">
                        🎓 Agent KHU
                    </h1>
                    <p className="text-sm text-gray-600 mt-1">
                        경희대학교 강의실 안내 AI
                    </p>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-4 py-6">
                <ChatInterface />
            </main>

            <footer className="text-center py-4 text-gray-600 text-sm">
                <p>경희대학교 국제캠퍼스 전자정보대학관</p>
            </footer>
        </div>
    );
}

export default App;