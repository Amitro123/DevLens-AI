import { useState } from 'react'
import UploadForm from './components/UploadForm'
import { FileVideo } from 'lucide-react'

function App() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
            {/* Header */}
            <header className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <div className="flex items-center gap-3">
                        <FileVideo className="w-8 h-8 text-blue-600" />
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">DocuFlow AI</h1>
                            <p className="text-sm text-gray-600 mt-1">
                                Transform videos into professional documentation
                            </p>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="bg-white rounded-lg shadow-lg p-8">
                    <div className="mb-8">
                        <h2 className="text-2xl font-semibold text-gray-800 mb-2">
                            Upload Your Video
                        </h2>
                        <p className="text-gray-600">
                            Select a documentation mode and upload your video. Our AI will analyze it and generate comprehensive documentation.
                        </p>
                    </div>

                    <UploadForm />
                </div>

                {/* Features */}
                <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white p-6 rounded-lg shadow">
                        <h3 className="font-semibold text-lg mb-2 text-blue-600">🐛 Bug Reports</h3>
                        <p className="text-gray-600 text-sm">
                            Automatically identify bugs and create detailed reproduction guides
                        </p>
                    </div>
                    <div className="bg-white p-6 rounded-lg shadow">
                        <h3 className="font-semibold text-lg mb-2 text-purple-600">📋 Feature Specs</h3>
                        <p className="text-gray-600 text-sm">
                            Generate comprehensive PRDs from feature demonstrations
                        </p>
                    </div>
                    <div className="bg-white p-6 rounded-lg shadow">
                        <h3 className="font-semibold text-lg mb-2 text-green-600">📚 Documentation</h3>
                        <p className="text-gray-600 text-sm">
                            Create step-by-step technical guides from tutorials
                        </p>
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="mt-16 pb-8 text-center text-gray-600 text-sm">
                <p>Powered by Google Gemini 1.5 Pro • Built with React & FastAPI</p>
            </footer>
        </div>
    )
}

export default App
