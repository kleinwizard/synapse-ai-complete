import { useState } from 'react';
import { ArrowLeft, Eye, EyeOff, Copy, Plus, Trash2, Key, User, Shield, CreditCard, ExternalLink, BarChart3 } from 'lucide-react';

interface User {
  id: string;
  email: string;
  name: string;
}

interface SettingsPageProps {
  user: User;
  onNavigate: (page: string) => void;
}

interface ApiKey {
  id: string;
  name: string;
  key: string;
  createdAt: string;
  lastUsed?: string;
}

const SettingsPage = ({ user, onNavigate }: SettingsPageProps) => {
  const [activeTab, setActiveTab] = useState('profile');
  const [isLoading, setIsLoading] = useState(false);
  const [showPasswords, setShowPasswords] = useState(false);
  
  // Profile state
  const [profileData, setProfileData] = useState({
    name: user.name,
    email: user.email,
  });

  // Password state
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  // API Keys state
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([
    {
      id: '1',
      name: 'Production API',
      key: 'syn_1234567890abcdef1234567890abcdef',
      createdAt: '2024-01-15',
      lastUsed: '2024-01-20'
    },
    {
      id: '2',
      name: 'Development API',
      key: 'syn_abcdef1234567890abcdef1234567890',
      createdAt: '2024-01-10',
      lastUsed: '2024-01-18'
    }
  ]);

  const [newKeyName, setNewKeyName] = useState('');
  const [showNewKeyDialog, setShowNewKeyDialog] = useState(false);

  const handleProfileSave = async () => {
    setIsLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch('http://localhost:8000/users/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          first_name: profileData.name.split(' ')[0] || '',
          last_name: profileData.name.split(' ').slice(1).join(' ') || '',
          email: profileData.email
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update profile');
      }

      const updatedUser = await response.json();
      localStorage.setItem('user', JSON.stringify(updatedUser));
      
      console.log('Profile updated successfully');
    } catch (error) {
      console.error('Profile update failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordChange = async () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      alert('Passwords do not match');
      return;
    }

    setIsLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch('http://localhost:8000/users/password', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: passwordData.currentPassword,
          new_password: passwordData.newPassword
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to change password');
      }

      console.log('Password changed successfully');
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
    } catch (error) {
      console.error('Password change failed:', error);
      alert('Failed to change password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const generateApiKey = async () => {
    if (!newKeyName.trim()) return;

    setIsLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch('http://localhost:8000/users/api-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: newKeyName
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate API key');
      }

      const newKeyData = await response.json();
      const newKey: ApiKey = {
        id: newKeyData.id.toString(),
        name: newKeyData.name,
        key: newKeyData.key,
        createdAt: newKeyData.created_at,
        lastUsed: newKeyData.last_used
      };

      setApiKeys([...apiKeys, newKey]);
      setNewKeyName('');
      setShowNewKeyDialog(false);
    } catch (error) {
      console.error('API key generation failed:', error);
      alert('Failed to generate API key. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const revokeApiKey = async (keyId: string) => {
    setIsLoading(true);
    
    try {
      // TODO: DEVIN - Replace with actual API key revocation
      // Expected endpoint: DELETE /api/users/api-keys/{keyId}
      // Expected response: { success: boolean }
      
      setApiKeys(apiKeys.filter(key => key.id !== keyId));
    } catch (error) {
      console.error('API key revocation failed:', error);
      // TODO: DEVIN - Add proper error handling and user feedback
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    const confirmDelete = confirm(
      'Are you absolutely sure you want to delete your account? This action cannot be undone and will permanently delete all your data, prompts, and subscription information.'
    );
    
    if (!confirmDelete) return;

    const finalConfirm = confirm(
      'This is your final warning. Type DELETE in the confirmation to proceed.'
    );
    
    if (!finalConfirm) return;

    setIsLoading(true);
    
    try {
      // TODO: DEVIN - Implement account deletion
      // Expected endpoint: DELETE /api/users/account
      // Expected payload: { confirmDelete: boolean }
      // Expected response: { success: boolean }
      // This should:
      // 1. Cancel any active subscriptions
      // 2. Delete all user data from database
      // 3. Revoke all API keys
      // 4. Delete Stripe customer if exists
      // 5. Log out user and redirect to landing page
      
      console.log('Account deletion requested');
    } catch (error) {
      console.error('Account deletion failed:', error);
      // TODO: DEVIN - Add proper error handling and user feedback
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignOut = async () => {
    try {
      // TODO: DEVIN - Implement sign out functionality
      // Expected endpoint: POST /api/auth/logout
      // Expected response: { success: boolean }
      // This should clear session and redirect to landing page
      
      console.log('Sign out requested');
    } catch (error) {
      console.error('Sign out failed:', error);
      // TODO: DEVIN - Add proper error handling
    }
  };

  const handleManageSubscription = async () => {
    setIsLoading(true);
    
    try {
      // TODO: DEVIN - Open Stripe Customer Portal for subscription management
      // Expected endpoint: POST /api/stripe/customer-portal
      // Expected payload: { userId: string }
      // Expected response: { portalUrl: string }
      // Redirect user to portal: window.open(portalUrl, '_blank');
      
      console.log('Opening subscription management portal');
    } catch (error) {
      console.error('Failed to open subscription portal:', error);
      // TODO: DEVIN - Add proper error handling and user feedback
    } finally {
      setIsLoading(false);
    }
  };

  const handleFetchBillingHistory = async () => {
    setIsLoading(true);
    
    try {
      // TODO: DEVIN - Fetch user's billing history
      // Expected endpoint: GET /api/users/billing-history
      // Expected response: { 
      //   invoices: Array<{
      //     id: string,
      //     date: string,
      //     amount: number,
      //     status: string,
      //     description: string,
      //     downloadUrl?: string
      //   }>
      // }
      // Display in modal or navigate to billing history page
      
      console.log('Fetching billing history');
    } catch (error) {
      console.error('Failed to fetch billing history:', error);
      // TODO: DEVIN - Add proper error handling and user feedback
    } finally {
      setIsLoading(false);
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

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'subscription', label: 'Subscription', icon: CreditCard },
    { id: 'api', label: 'API Keys', icon: Key },
  ];

  return (
    <div className="min-h-screen bg-synapse-background">
      {/* Header */}
      <header className="border-b border-synapse-border px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => onNavigate('workspace')}
              className="text-synapse-text-muted hover:text-synapse-text transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div className="text-2xl font-bold text-synapse-primary">
              Synapse
            </div>
          </div>
          
          <div className="text-sm text-synapse-text">
            Account Settings
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-synapse-text-bright mb-2">
            Account Settings
          </h1>
          <p className="text-synapse-text-muted">
            Manage your account preferences and security settings
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Tab Navigation */}
          <div className="lg:w-64">
            <nav className="space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center px-4 py-3 text-left rounded-lg transition-all duration-200 ${
                      activeTab === tab.id
                        ? 'bg-synapse-primary text-synapse-primary-foreground'
                        : 'text-synapse-text-muted hover:text-synapse-text hover:bg-synapse-hover'
                    }`}
                  >
                    <Icon className="h-5 w-5 mr-3" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="flex-1">
            {activeTab === 'profile' && (
              <div className="synapse-card">
                <h2 className="text-xl font-semibold text-synapse-text-bright mb-6">
                  Profile Information
                </h2>
                
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-synapse-text mb-2">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={profileData.name}
                      onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                      className="synapse-input w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-synapse-text mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={profileData.email}
                      onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                      className="synapse-input w-full"
                    />
                  </div>

                  <button
                    onClick={handleProfileSave}
                    disabled={isLoading}
                    className="bg-synapse-primary hover:bg-synapse-primary-hover text-synapse-primary-foreground font-medium py-2 px-4 rounded-lg transition-all duration-200 disabled:opacity-50 flex items-center"
                  >
                    {isLoading ? (
                      <>
                        <div className="spinner mr-2" />
                        Saving...
                      </>
                    ) : (
                      'Save Changes'
                    )}
                  </button>

                  {/* Delete Account Section */}
                  <div className="border-t border-synapse-border pt-6 mt-8">
                    <h3 className="text-lg font-semibold text-synapse-error mb-4">
                      Danger Zone
                    </h3>
                    <div className="bg-synapse-error/10 border border-synapse-error/20 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-medium text-synapse-error mb-2">
                            Delete Account
                          </h4>
                          <p className="text-sm text-synapse-text-muted mb-4">
                            Permanently delete your account and all associated data. This action cannot be undone.
                          </p>
                        </div>
                        <button
                          onClick={handleDeleteAccount}
                          disabled={isLoading}
                          className="bg-synapse-error hover:bg-red-600 text-white font-medium py-2 px-4 rounded-lg transition-all duration-200 disabled:opacity-50 flex items-center ml-4"
                        >
                          {isLoading ? (
                            <>
                              <div className="spinner mr-2" />
                              Deleting...
                            </>
                          ) : (
                            'Delete Account'
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="synapse-card">
                <h2 className="text-xl font-semibold text-synapse-text-bright mb-6">
                  Change Password
                </h2>
                
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-synapse-text mb-2">
                      Current Password
                    </label>
                    <div className="relative">
                      <input
                        type={showPasswords ? 'text' : 'password'}
                        value={passwordData.currentPassword}
                        onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                        className="synapse-input w-full pr-12"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPasswords(!showPasswords)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-synapse-text-muted hover:text-synapse-text"
                      >
                        {showPasswords ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-synapse-text mb-2">
                      New Password
                    </label>
                    <input
                      type={showPasswords ? 'text' : 'password'}
                      value={passwordData.newPassword}
                      onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                      className="synapse-input w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-synapse-text mb-2">
                      Confirm New Password
                    </label>
                    <input
                      type={showPasswords ? 'text' : 'password'}
                      value={passwordData.confirmPassword}
                      onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                      className="synapse-input w-full"
                    />
                  </div>

                  <button
                    onClick={handlePasswordChange}
                    disabled={isLoading || !passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword}
                    className="bg-synapse-primary hover:bg-synapse-primary-hover text-synapse-primary-foreground font-medium py-2 px-4 rounded-lg transition-all duration-200 disabled:opacity-50 flex items-center"
                  >
                    {isLoading ? (
                      <>
                        <div className="spinner mr-2" />
                        Updating...
                      </>
                    ) : (
                      'Update Password'
                    )}
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'subscription' && (
              <div className="synapse-card">
                <h2 className="text-xl font-semibold text-synapse-text-bright mb-6">
                  Subscription Management
                </h2>
                
                <div className="space-y-6">
                  <div className="bg-synapse-surface border border-synapse-border rounded-lg p-6">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium text-synapse-text mb-2">Current Plan</h3>
                        <p className="text-2xl font-bold text-synapse-primary mb-1">Basic Plan</p>
                        <p className="text-sm text-synapse-text-muted">100 credits per month</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-synapse-text-muted">Next billing</p>
                        <p className="font-medium text-synapse-text">No active subscription</p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <button
                      onClick={() => onNavigate('subscription')}
                      className="w-full bg-synapse-primary hover:bg-synapse-primary-hover text-synapse-primary-foreground font-medium py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center"
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      View All Plans & Pricing
                    </button>

                    <button
                      onClick={handleManageSubscription}
                      disabled={isLoading}
                      className="w-full border border-synapse-border text-synapse-text hover:bg-synapse-hover font-medium py-3 px-4 rounded-lg transition-all duration-200 disabled:opacity-50 flex items-center justify-center"
                    >
                      {isLoading ? (
                        <>
                          <div className="spinner mr-2" />
                          Loading...
                        </>
                      ) : (
                        <>
                          <ExternalLink className="h-4 w-4 mr-2" />
                          Manage Subscription
                        </>
                      )}
                    </button>

                    <button
                      onClick={handleFetchBillingHistory}
                      disabled={isLoading}
                      className="w-full border border-synapse-border text-synapse-text hover:bg-synapse-hover font-medium py-3 px-4 rounded-lg transition-all duration-200 disabled:opacity-50 flex items-center justify-center"
                    >
                      {isLoading ? (
                        <>
                          <div className="spinner mr-2" />
                          Loading...
                        </>
                      ) : (
                        <>
                          <BarChart3 className="h-4 w-4 mr-2" />
                          View Billing History
                        </>
                      )}
                    </button>

                    <p className="text-sm text-synapse-text-muted text-center">
                      Upgrade to Pro or Enterprise for more credits, advanced features, and priority support.
                    </p>
                  </div>

                  {/* TODO: DEVIN - Add subscription management functionality */}
                  {/* Expected features:
                      - Display current subscription tier and status
                      - Show next billing date and amount
                      - Cancel subscription button (with confirmation)
                      - Update payment method button
                      - View billing history
                      - Expected endpoints:
                        - GET /api/users/subscription (current status)
                        - POST /api/stripe/customer-portal (manage subscription)
                        - GET /api/users/billing-history (payment history)
                  */}
                </div>
              </div>
            )}

            {activeTab === 'api' && (
              <div className="space-y-6">
                <div className="synapse-card">
                  <div className="flex justify-between items-center mb-6">
                    <div>
                      <h2 className="text-xl font-semibold text-synapse-text-bright">
                        API Keys
                      </h2>
                      <p className="text-sm text-synapse-text-muted mt-1">
                        Use these keys to access the Synapse API programmatically
                      </p>
                    </div>
                    <button
                      onClick={() => setShowNewKeyDialog(true)}
                      className="bg-synapse-primary hover:bg-synapse-primary-hover text-synapse-primary-foreground font-medium py-2 px-4 rounded-lg transition-all duration-200 flex items-center"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Generate Key
                    </button>
                  </div>

                  <div className="space-y-4">
                    {apiKeys.map((apiKey) => (
                      <div key={apiKey.id} className="bg-synapse-surface border border-synapse-border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h3 className="font-medium text-synapse-text">{apiKey.name}</h3>
                            <p className="text-sm text-synapse-text-muted">
                              Created: {new Date(apiKey.createdAt).toLocaleDateString()}
                              {apiKey.lastUsed && (
                                <span className="ml-4">
                                  Last used: {new Date(apiKey.lastUsed).toLocaleDateString()}
                                </span>
                              )}
                            </p>
                          </div>
                          <button
                            onClick={() => revokeApiKey(apiKey.id)}
                            disabled={isLoading}
                            className="text-synapse-error hover:text-red-400 transition-colors p-1"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <code className="flex-1 bg-synapse-background border border-synapse-border rounded px-3 py-2 text-sm text-synapse-text-muted font-mono">
                            {apiKey.key}
                          </code>
                          <button
                            onClick={() => copyToClipboard(apiKey.key)}
                            className="bg-synapse-primary/10 text-synapse-primary p-2 rounded hover:bg-synapse-primary/20 transition-colors"
                          >
                            <Copy className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ))}

                    {apiKeys.length === 0 && (
                      <div className="text-center py-8 text-synapse-text-muted">
                        <Key className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No API keys generated yet</p>
                        <p className="text-sm">Create your first API key to get started</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* New Key Dialog */}
                {showNewKeyDialog && (
                  <div className="synapse-card">
                    <h3 className="text-lg font-semibold text-synapse-text-bright mb-4">
                      Generate New API Key
                    </h3>
                    
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-synapse-text mb-2">
                          Key Name
                        </label>
                        <input
                          type="text"
                          value={newKeyName}
                          onChange={(e) => setNewKeyName(e.target.value)}
                          placeholder="e.g., Production API, Development, etc."
                          className="synapse-input w-full"
                        />
                      </div>

                      <div className="flex space-x-3">
                        <button
                          onClick={generateApiKey}
                          disabled={isLoading || !newKeyName.trim()}
                          className="bg-synapse-primary hover:bg-synapse-primary-hover text-synapse-primary-foreground font-medium py-2 px-4 rounded-lg transition-all duration-200 disabled:opacity-50 flex items-center"
                        >
                          {isLoading ? (
                            <>
                              <div className="spinner mr-2" />
                              Generating...
                            </>
                          ) : (
                            'Generate Key'
                          )}
                        </button>
                        <button
                          onClick={() => {
                            setShowNewKeyDialog(false);
                            setNewKeyName('');
                          }}
                          className="border border-synapse-border text-synapse-text hover:bg-synapse-hover font-medium py-2 px-4 rounded-lg transition-all duration-200"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
