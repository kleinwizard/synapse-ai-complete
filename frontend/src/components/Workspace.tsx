import { useState, useEffect } from 'react';
import { User, Copy, Sparkles } from 'lucide-react';

interface User {
  id: string;
  email: string;
  name: string;
}

interface WorkspaceProps {
  user: User;
  onNavigate: (page: string) => void;
}

const powerLevels = [
  { 
    id: 'low', 
    label: 'Low', 
    cost: 25,
    description: 'Basic prompt enhancement with structure and clarity improvements. Perfect for simple tasks and everyday use cases.'
  },
  { 
    id: 'med', 
    label: 'Med', 
    cost: 50,
    description: 'Moderate enhancement with expert techniques, context setting, and optimization strategies. Great for professional work.'
  },
  { 
    id: 'high', 
    label: 'High', 
    cost: 100,
    description: 'Advanced prompt engineering with sophisticated frameworks, multiple perspectives, and detailed guidelines. Ideal for complex projects.'
  },
  { 
    id: 'pro', 
    label: 'Pro', 
    cost: 200,
    description: 'Maximum enhancement with cutting-edge techniques, comprehensive context, role definitions, and expert-level optimization. For critical applications.'
  },
];

const Workspace = ({ user, onNavigate }: WorkspaceProps) => {
  const [selectedPower, setSelectedPower] = useState('med');
  const [userInput, setUserInput] = useState('');
  const [activeTab, setActiveTab] = useState('output');
  const [isGenerating, setIsGenerating] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [finalOutput, setFinalOutput] = useState('');
  const [synapsePrompt, setSynapsePrompt] = useState('');
  const [credits, setCredits] = useState(0);

  const handleSignOut = async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      }
      
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      onNavigate('auth');
    } catch (error) {
      console.error('Sign out failed:', error);
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      onNavigate('auth');
    }
  };

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/users/me`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setCredits(userData.credits || 0);
        }
      } catch (error) {
        console.error('Failed to fetch user data:', error);
      }
    };

    fetchUserData();
  }, []);

  const selectedLevel = powerLevels.find(level => level.id === selectedPower);

  // Task classification function
  const classifyTask = (prompt: string): string => {
    const lowerPrompt = prompt.toLowerCase();
    
    // Code-related keywords
    if (lowerPrompt.includes('code') || lowerPrompt.includes('programming') || 
        lowerPrompt.includes('function') || lowerPrompt.includes('algorithm') ||
        lowerPrompt.includes('debug') || lowerPrompt.includes('javascript') ||
        lowerPrompt.includes('python') || lowerPrompt.includes('react') ||
        lowerPrompt.includes('api') || lowerPrompt.includes('database')) {
      return 'code';
    }
    
    // Research-related keywords
    if (lowerPrompt.includes('research') || lowerPrompt.includes('analyze') ||
        lowerPrompt.includes('study') || lowerPrompt.includes('investigate') ||
        lowerPrompt.includes('compare') || lowerPrompt.includes('report') ||
        lowerPrompt.includes('data') || lowerPrompt.includes('statistics')) {
      return 'research';
    }
    
    // Writing-related keywords
    if (lowerPrompt.includes('write') || lowerPrompt.includes('essay') ||
        lowerPrompt.includes('article') || lowerPrompt.includes('blog') ||
        lowerPrompt.includes('content') || lowerPrompt.includes('copy')) {
      return 'writing';
    }
    
    return 'default';
  };

  // Map frontend power levels to backend power levels
  const mapPowerLevel = (frontendLevel: string): string => {
    const mapping = {
      'low': 'low',
      'med': 'med', 
      'high': 'high',
      'pro': 'pro'
    };
    return mapping[frontendLevel as keyof typeof mapping] || 'med';
  };

  const handleGenerate = async () => {
    if (!userInput.trim() || !selectedPower) return;

    const selectedLevel = powerLevels.find(level => level.id === selectedPower);
    if (!selectedLevel) return;

    setIsGenerating(true);
    setActiveTab('output');
    setStreamingText('');
    setFinalOutput('');
    setSynapsePrompt('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication required. Please log in again.');
      }

      // Classify the task type
      const taskType = classifyTask(userInput);
      const powerLevel = mapPowerLevel(selectedPower);

      // Call the optimize endpoint
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/optimize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          prompt: userInput,
          task_description: `Enhance this ${taskType} prompt with ${powerLevel} level optimization`,
          role: taskType === 'code' ? 'senior software engineer' : 
                taskType === 'research' ? 'expert researcher' : 
                taskType === 'writing' ? 'professional writer' : 'professional assistant',
          tone: 'helpful and analytical',
          deliverable_format: 'markdown',
          parameters: {
            power_level: powerLevel,
            task_type: taskType,
            enhancement_level: selectedPower
          }
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Extract the correct data from the response
      const optimizedPrompt = data.synapse_prompt || 'No enhanced prompt generated';
      const finalOutput = data.final_output || 'No final output generated';
      
      // Show the final output with streaming effect
      for (let i = 0; i < finalOutput.length; i += 20) {
        await new Promise(resolve => setTimeout(resolve, 25));
        setStreamingText(finalOutput.slice(0, i + 20));
      }

      // Set the final states
      setFinalOutput(finalOutput);  // This is the API LLM's response to the optimized prompt
      setSynapsePrompt(optimizedPrompt);  // This is the optimized prompt created by local LLM
      setCredits(prev => prev - selectedLevel.cost);
      
    } catch (error) {
      console.error('Prompt generation failed:', error);
      alert(`Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // You could add a toast notification here
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <div className="min-h-screen bg-synapse-background">
      {/* Header */}
      <header className="border-b border-synapse-border px-6 py-4">
        <div className="flex justify-between items-center max-w-7xl mx-auto">
          <div className="text-2xl font-bold text-synapse-primary">
            Synapse
          </div>
          
          <div className="flex items-center space-x-6">
            <button 
              onClick={() => onNavigate('subscription')}
              className="text-sm text-synapse-text hover:text-synapse-primary transition-colors"
            >
              Credits: <span className="font-semibold text-synapse-primary">{credits.toLocaleString()}</span>
            </button>
            
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-synapse-primary rounded-full flex items-center justify-center">
                <User className="h-4 w-4 text-synapse-primary-foreground" />
              </div>
              <div className="flex items-center space-x-4">
                <button 
                  onClick={() => onNavigate('settings')}
                  className="text-synapse-text hover:text-synapse-primary transition-colors"
                >
                  {user.name}
                </button>
                <button
                  onClick={handleSignOut}
                  className="text-sm text-synapse-text-muted hover:text-synapse-error transition-colors"
                >
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-2 gap-8 h-[calc(100vh-120px)]">
          {/* Input Section */}
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold text-synapse-text-bright mb-2">
                Transform Your Ideas
              </h1>
              <p className="text-synapse-text-muted">
                Enter your basic concept and watch Synapse create expert-level prompts
              </p>
              
              {/* TEMPORARY DEMO BUTTON - REMOVE AFTER TESTING */}
              <button 
                onClick={() => setCredits(prev => prev + 1000)}
                className="text-xs bg-red-600 text-white px-2 py-1 rounded"
                style={{fontSize: '10px'}}
              >
                +1000 Demo Credits (TEMP)
              </button>
            </div>

            {/* Power Level Selector */}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-synapse-text">
                Enhancement Level
              </label>
              <div className="power-selector">
                {powerLevels.map((level) => (
                  <button
                    key={level.id}
                    onClick={() => setSelectedPower(level.id)}
                    className={`power-option ${selectedPower === level.id ? 'active' : ''}`}
                  >
                    {level.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Dynamic Description */}
            {selectedLevel && (
              <div className="synapse-card bg-synapse-surface/50">
                <div className="flex items-start space-x-3">
                  <Sparkles className="h-5 w-5 text-synapse-primary mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-synapse-text mb-1">
                      {selectedLevel.label} Enhancement ({selectedLevel.cost} credits)
                    </div>
                    <div className="text-sm text-synapse-text-muted">
                      {selectedLevel.description}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Input Area */}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-synapse-text">
                Your Prompt Idea
              </label>
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="Enter your basic idea here... (e.g., 'Help me write a marketing email', 'Create a sales presentation', 'Write a product description')"
                className="synapse-input w-full h-32 resize-none"
              />
            </div>

            {/* Task Classification Display */}
            {userInput.trim() && (
              <div className="text-xs text-synapse-text-muted mb-3">
                Detected task type: <span className="text-synapse-primary font-medium">
                  {classifyTask(userInput)}
                </span>
              </div>
            )}

            {/* Generate Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !userInput.trim() || credits < selectedLevel!.cost}
              className="w-full bg-synapse-primary hover:bg-synapse-primary-hover text-synapse-primary-foreground font-semibold py-4 px-6 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isGenerating ? (
                <>
                  <div className="spinner mr-2" />
                  Generating...
                </>
              ) : (
                `Generate [${selectedLevel?.cost} Credits]`
              )}
            </button>

            {credits < selectedLevel!.cost && (
              <div className="text-sm text-synapse-error text-center">
                Insufficient credits. 
                <button 
                  onClick={() => onNavigate('billing')}
                  className="text-synapse-primary hover:underline ml-1"
                >
                  Top up now
                </button>
              </div>
            )}
          </div>

          {/* Output Section */}
          <div className="flex flex-col">
            {/* Tabs */}
            <div className="flex border-b border-synapse-border mb-6">
              <button
                onClick={() => setActiveTab('output')}
                className={`tab-button ${activeTab === 'output' ? 'active' : ''}`}
              >
                Final Output
              </button>
              <button
                onClick={() => setActiveTab('prompt')}
                className={`tab-button ${activeTab === 'prompt' ? 'active' : ''}`}
              >
                Synapse Prompt
              </button>
            </div>

            {/* Content Area */}
            <div className="flex-1 synapse-card bg-synapse-surface overflow-hidden">
              {activeTab === 'output' ? (
                <div className="h-full">
                  {!finalOutput && !streamingText && !isGenerating && (
                    <div className="h-full flex items-center justify-center text-synapse-text-muted">
                      <div className="text-center">
                        <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>Your enhanced prompt will appear here</p>
                      </div>
                    </div>
                  )}
                  
                  {(streamingText || finalOutput) && (
                    <div className="h-full overflow-auto">
                      <pre className="text-sm text-synapse-text leading-relaxed whitespace-pre-wrap">
                        {isGenerating ? streamingText : finalOutput}
                        {isGenerating && <span className="animate-pulse">|</span>}
                      </pre>
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-full">
                  {!synapsePrompt && (
                    <div className="h-full flex items-center justify-center text-synapse-text-muted">
                      <div className="text-center">
                        <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>Generate a prompt to see the Synapse meta-prompt</p>
                      </div>
                    </div>
                  )}
                  
                  {synapsePrompt && (
                    <div className="h-full flex flex-col">
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="font-medium text-synapse-text">Enhanced Prompt Structure</h3>
                        <button
                          onClick={() => copyToClipboard(synapsePrompt)}
                          className="flex items-center space-x-2 px-3 py-1.5 bg-synapse-primary/10 text-synapse-primary rounded-lg hover:bg-synapse-primary/20 transition-colors text-sm"
                        >
                          <Copy className="h-4 w-4" />
                          <span>Copy Prompt</span>
                        </button>
                      </div>
                      <div className="flex-1 overflow-auto">
                        <pre className="text-sm text-synapse-text leading-relaxed whitespace-pre-wrap">
                          {synapsePrompt}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Workspace;
