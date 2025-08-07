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

  const handleGenerate = async () => {
    if (!userInput.trim()) return;

    setIsGenerating(true);
    setStreamingText('');
    setFinalOutput('');
    setSynapsePrompt('');
    setActiveTab('output');

    try {
      // TODO: DEVIN - Replace with actual prompt generation API call
      // Expected endpoint: POST /api/prompts/generate
      // Expected payload: { 
      //   input: string, 
      //   powerLevel: 'low' | 'med' | 'high' | 'pro',
      //   userId: string 
      // }
      // Expected response: { 
      //   finalOutput: string, 
      //   synapsePrompt: string, 
      //   creditsUsed: number,
      //   stream?: boolean 
      // }
      // For streaming: use EventSource or WebSocket for real-time text updates
    const mockOutput = `# Enhanced Marketing Email Prompt

## Context & Expertise
You are a senior marketing strategist with 15+ years of experience in email marketing campaigns. You've successfully increased open rates by 40% and conversion rates by 65% across Fortune 500 companies.

## Objective
Create a compelling marketing email that drives ${userInput.includes('sales') ? 'sales conversions' : 'user engagement'} for the specified product/service.

## Target Analysis
- **Primary Audience**: [Define demographics, psychographics, pain points]
- **Secondary Audience**: [Identify potential secondary markets]
- **Customer Journey Stage**: [Awareness/Consideration/Decision/Retention]

## Email Structure Framework
1. **Subject Line Strategy**
   - Primary: [Action-oriented with urgency]
   - A/B Test Variant: [Curiosity-driven approach]
   - Emoji usage: [Strategic placement for mobile optimization]

2. **Opening Hook** (First 50 words)
   - Personalization token
   - Immediate value proposition
   - Problem acknowledgment

3. **Value Proposition Section**
   - Core benefit statement
   - Quantified results/outcomes
   - Social proof integration

4. **Call-to-Action Engineering**
   - Primary CTA: [Specific action verb]
   - Secondary CTA: [Lower commitment option]
   - Visual hierarchy considerations

## Psychological Triggers
- Scarcity principle implementation
- Authority positioning
- Social proof integration
- Loss aversion techniques

## Technical Specifications
- Mobile-first design considerations
- Accessibility requirements
- A/B testing elements
- Tracking parameters

## Deliverables
Provide complete email copy with subject line variations, design notes, and psychological trigger explanations.`;

    const mockSynapsePrompt = `# Synapse Meta-Prompt for Marketing Email Enhancement

## System Context
Transform the user's basic request "${userInput}" into a comprehensive marketing email creation prompt using advanced prompt engineering techniques.

## Enhancement Framework Applied
- **Role Definition**: Senior marketing strategist persona
- **Context Layering**: Industry expertise + specific domain knowledge
- **Constraint Setting**: Technical and strategic parameters
- **Output Structuring**: Hierarchical deliverable breakdown
- **Psychological Framework**: Influence principles integration

## Prompt Engineering Techniques Used
1. Persona-based role assignment
2. Multi-layered context establishment
3. Structured output formatting
4. Psychological trigger integration
5. Technical specification inclusion
6. Deliverable clarity definition

## Quality Assurance Metrics
- Specificity Level: High
- Actionability Score: 95%
- Context Richness: Comprehensive
- Output Predictability: Structured

This meta-prompt demonstrates how Synapse transforms simple inputs into expert-level instructions through systematic enhancement protocols.`;

      // TODO: DEVIN - Remove this simulation and implement real streaming
      // For streaming implementation:
      // 1. Set up EventSource or WebSocket connection
      // 2. Listen for text chunks and update streamingText state
      // 3. Handle completion and set final states
      
      for (let i = 0; i < mockOutput.length; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 50));
        setStreamingText(mockOutput.slice(0, i + 10));
      }

      setFinalOutput(mockOutput);
      setSynapsePrompt(mockSynapsePrompt);
      setCredits(prev => prev - selectedLevel!.cost);
      
    } catch (error) {
      console.error('Prompt generation failed:', error);
      // TODO: DEVIN - Add proper error handling and user feedback
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
