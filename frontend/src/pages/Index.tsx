import { useState } from 'react';
import LandingPage from '@/components/LandingPage';
import AuthPage from '@/components/AuthPage';
import Workspace from '@/components/Workspace';
import BillingPage from '@/components/BillingPage';
import SubscriptionPage from '@/components/SubscriptionPage';
import SettingsPage from '@/components/SettingsPage';
import WelcomeModal from '@/components/WelcomeModal';

interface User {
  id: string;
  email: string;
  name: string;
}

type PageType = 'landing' | 'auth' | 'workspace' | 'billing' | 'subscription' | 'settings';

const Index = () => {
  const [currentPage, setCurrentPage] = useState<PageType>('landing');
  const [user, setUser] = useState<User | null>(() => {
    const savedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    return savedUser && token ? JSON.parse(savedUser) : null;
  });
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);

  const handleAuthSuccess = (userData: User) => {
    setUser(userData);
    setCurrentPage('workspace');
    
    const onboardingCompleted = localStorage.getItem('onboarding_completed');
    if (!onboardingCompleted) {
      setShowWelcomeModal(true);
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setCurrentPage('auth');
  };

  const handleNavigation = (page: PageType) => {
    setCurrentPage(page);
  };

  const handleGetStarted = () => {
    if (user) {
      setCurrentPage('workspace');
    } else {
      setCurrentPage('auth');
    }
  };

  // Landing Page
  if (currentPage === 'landing') {
    return <LandingPage onGetStarted={handleGetStarted} />;
  }

  // Authentication
  if (currentPage === 'auth') {
    return <AuthPage onAuthSuccess={handleAuthSuccess} />;
  }

  // Protected routes - require authentication
  if (!user) {
    return <AuthPage onAuthSuccess={handleAuthSuccess} />;
  }

  // Main Workspace
  if (currentPage === 'workspace') {
    return (
      <>
        <Workspace user={user} onNavigate={handleNavigation} />
        <WelcomeModal 
          isOpen={showWelcomeModal} 
          onClose={() => setShowWelcomeModal(false)} 
        />
      </>
    );
  }

  // Subscription Page
  if (currentPage === 'subscription') {
    return <SubscriptionPage user={user} onNavigate={handleNavigation} />;
  }

  // Billing Page
  if (currentPage === 'billing') {
    return <BillingPage user={user} onNavigate={handleNavigation} />;
  }

  // Settings Page
  if (currentPage === 'settings') {
    return <SettingsPage user={user} onNavigate={handleNavigation} />;
  }

  // Fallback
  return <LandingPage onGetStarted={handleGetStarted} />;
};

export default Index;
