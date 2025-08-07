import { useState, useEffect } from 'react';
import { ArrowLeft, Check, Zap, CreditCard, Star, Shield, Headphones, Code, Users, BarChart3 } from 'lucide-react';

interface User {
  id: string;
  email: string;
  name: string;
}

interface SubscriptionPageProps {
  user: User;
  onNavigate: (page: string) => void;
}

const plans = [
  {
    id: 'basic',
    name: 'Basic',
    description: 'Perfect for individuals getting started',
    price: 0,
    credits: 100,
    features: [
      '100 credits per month',
      'Basic power levels (Low, Med)',
      'Standard templates',
      'Community support',
      'Email support',
      'Basic analytics'
    ],
    popular: false,
    buttonText: 'Current Plan',
    buttonVariant: 'secondary'
  },
  {
    id: 'pro',
    name: 'Pro',
    description: 'For professionals and growing teams',
    price: 29,
    credits: 2000,
    features: [
      '2,000 credits per month',
      'All power levels (Low, Med, High, Pro)',
      'Premium templates & frameworks',
      'Priority email support',
      'API access (10,000 calls/month)',
      'Advanced analytics & insights',
      'Export to multiple formats',
      'Custom prompt libraries'
    ],
    popular: true,
    buttonText: 'Upgrade to Pro',
    buttonVariant: 'primary'
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    description: 'For large teams and organizations',
    price: 99,
    credits: 'Unlimited',
    features: [
      'Unlimited credits',
      'Custom power levels',
      'Enterprise templates & frameworks',
      'Dedicated account manager',
      'Unlimited API access',
      'Advanced team analytics',
      'Custom integrations',
      'SSO & user management',
      'SLA guarantee (99.9% uptime)',
      'Custom training & onboarding'
    ],
    popular: false,
    buttonText: 'Contact Sales',
    buttonVariant: 'secondary'
  }
];

const creditPacks = [
  {
    credits: 500,
    price: 12,
    bonus: 0,
    popular: false,
    description: 'Perfect for occasional use'
  },
  {
    credits: 1000,
    price: 20,
    bonus: 100,
    popular: true,
    description: 'Most popular choice'
  },
  {
    credits: 2500,
    price: 45,
    bonus: 350,
    popular: false,
    description: 'Best value for heavy users'
  },
  {
    credits: 5000,
    price: 80,
    bonus: 1000,
    popular: false,
    description: 'For enterprise usage'
  }
];

const SubscriptionPage = ({ user, onNavigate }: SubscriptionPageProps) => {
  const [activeTab, setActiveTab] = useState('plans');
  const [isLoading, setIsLoading] = useState(false);
  const [currentPlan, setCurrentPlan] = useState('basic');
  const [userCredits, setUserCredits] = useState(0);

  useEffect(() => {
    const fetchSubscriptionData = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        const response = await fetch('http://localhost:8000/users/subscription', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setCurrentPlan(data.current_plan || 'basic');
          setUserCredits(data.credits || 0);
        }
      } catch (error) {
        console.error('Failed to fetch subscription data:', error);
      }
    };

    fetchSubscriptionData();
  }, []);

  const handlePlanUpgrade = async (planId: string) => {
    if (planId === 'enterprise') {
      window.open('mailto:sales@synapse.com?subject=Enterprise Plan Inquiry', '_blank');
      return;
    }

    setIsLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch('http://localhost:8000/stripe/create-checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          plan_id: planId,
          success_url: `${window.location.origin}/subscription?success=true`,
          cancel_url: `${window.location.origin}/subscription?canceled=true`
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create checkout session');
      }

      const data = await response.json();
      window.open(data.checkout_url, '_blank');
    } catch (error) {
      console.error('Plan upgrade failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChangePlan = async () => {
    setIsLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch('http://localhost:8000/stripe/customer-portal', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to create customer portal session');
      }

      const data = await response.json();
      window.open(data.portal_url, '_blank');
    } catch (error) {
      console.error('Failed to open plan change portal:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreditPurchase = async (pack: typeof creditPacks[0]) => {
    setIsLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch('http://localhost:8000/stripe/create-credit-checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          credits: pack.credits + pack.bonus,
          amount: pack.price,
          success_url: `${window.location.origin}/subscription?success=true`,
          cancel_url: `${window.location.origin}/subscription?canceled=true`
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create checkout session');
      }

      const data = await response.json();
      window.open(data.checkout_url, '_blank');
    } catch (error) {
      console.error('Credit purchase failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    { id: 'plans', label: 'Subscription Plans', icon: Star },
    { id: 'credits', label: 'Credit Packs', icon: Zap },
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
          
          <div className="flex items-center space-x-4">
            <div className="text-sm text-synapse-text">
              Credits: <span className="font-semibold text-synapse-primary">{userCredits.toLocaleString()}</span>
            </div>
            <div className="text-sm text-synapse-text">
              {user.name}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-synapse-text-bright mb-4">
            Choose Your Plan
          </h1>
          <p className="text-lg text-synapse-text-muted max-w-2xl mx-auto">
            Unlock the full potential of Synapse with our flexible subscription plans and credit packages. 
            Scale as you grow with transparent pricing.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex justify-center mb-12">
          <div className="flex bg-synapse-surface border border-synapse-border rounded-lg p-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center px-6 py-3 rounded-md text-sm font-medium transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'bg-synapse-primary text-synapse-primary-foreground shadow-sm'
                      : 'text-synapse-text-muted hover:text-synapse-text'
                  }`}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Plans Tab */}
        {activeTab === 'plans' && (
          <div className="space-y-12">
            <div className="grid lg:grid-cols-3 gap-8">
              {plans.map((plan) => (
                <div
                  key={plan.id}
                  className={`relative overflow-hidden rounded-2xl border transition-all duration-200 ${
                    plan.popular
                      ? 'border-synapse-primary bg-synapse-primary/5 scale-105 shadow-lg'
                      : currentPlan === plan.id
                      ? 'border-synapse-primary bg-synapse-primary/5'
                      : 'border-synapse-border bg-synapse-card hover:border-synapse-primary/30'
                  }`}
                >
                  {plan.popular && (
                    <div className="absolute top-0 left-0 right-0 bg-synapse-primary text-synapse-primary-foreground text-center py-2 text-sm font-medium">
                      Most Popular
                    </div>
                  )}
                  
                  {currentPlan === plan.id && !plan.popular && (
                    <div className="absolute top-0 left-0 right-0 bg-synapse-success text-white text-center py-2 text-sm font-medium">
                      Current Plan
                    </div>
                  )}

                  <div className={`p-8 ${plan.popular || currentPlan === plan.id ? 'pt-12' : ''}`}>
                    <div className="text-center mb-8">
                      <h3 className="text-2xl font-bold text-synapse-text-bright mb-2">
                        {plan.name}
                      </h3>
                      <p className="text-synapse-text-muted mb-4">
                        {plan.description}
                      </p>
                      <div className="flex items-baseline justify-center">
                        <span className="text-4xl font-bold text-synapse-primary">
                          ${plan.price}
                        </span>
                        <span className="text-synapse-text-muted ml-1">/month</span>
                      </div>
                      <div className="text-sm text-synapse-text-muted mt-2">
                        {typeof plan.credits === 'number' 
                          ? `${plan.credits.toLocaleString()} credits included`
                          : plan.credits
                        }
                      </div>
                    </div>

                    <ul className="space-y-4 mb-8">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-start">
                          <Check className="h-5 w-5 text-synapse-success mr-3 mt-0.5 flex-shrink-0" />
                          <span className="text-sm text-synapse-text">{feature}</span>
                        </li>
                      ))}
                    </ul>

                    <button
                      onClick={() => plan.id !== 'basic' && handlePlanUpgrade(plan.id)}
                      disabled={isLoading || currentPlan === plan.id}
                      className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-200 ${
                        currentPlan === plan.id
                          ? 'bg-synapse-surface text-synapse-text-muted cursor-not-allowed'
                          : plan.buttonVariant === 'primary'
                          ? 'bg-synapse-primary text-synapse-primary-foreground hover:bg-synapse-primary-hover shadow-lg'
                          : 'border border-synapse-border text-synapse-text hover:bg-synapse-hover'
                      }`}
                    >
                      {isLoading ? (
                        <div className="flex items-center justify-center">
                          <div className="spinner mr-2" />
                          Processing...
                        </div>
                      ) : currentPlan === plan.id ? (
                        'Current Plan'
                      ) : (
                        plan.buttonText
                      )}
                    </button>

                    {/* Change Plan Button for Current Plan */}
                    {currentPlan === plan.id && plan.id !== 'basic' && (
                      <button
                        onClick={handleChangePlan}
                        disabled={isLoading}
                        className="w-full mt-2 border border-synapse-border text-synapse-text hover:bg-synapse-hover font-medium py-2 px-4 rounded-lg transition-all duration-200 disabled:opacity-50 flex items-center justify-center"
                      >
                        {isLoading ? (
                          <>
                            <div className="spinner mr-2" />
                            Loading...
                          </>
                        ) : (
                          'Change Plan'
                        )}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Plan Comparison */}
            <div className="bg-synapse-card border border-synapse-border rounded-xl p-8">
              <h3 className="text-xl font-semibold text-synapse-text-bright mb-6 text-center">
                Plan Comparison
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-synapse-border">
                      <th className="text-left py-3 text-synapse-text-muted">Feature</th>
                      <th className="text-center py-3 text-synapse-text-muted">Basic</th>
                      <th className="text-center py-3 text-synapse-text-muted">Pro</th>
                      <th className="text-center py-3 text-synapse-text-muted">Enterprise</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    <tr className="border-b border-synapse-border/50">
                      <td className="py-3 text-synapse-text">Monthly Credits</td>
                      <td className="text-center py-3 text-synapse-text-muted">100</td>
                      <td className="text-center py-3 text-synapse-text-muted">2,000</td>
                      <td className="text-center py-3 text-synapse-text-muted">Unlimited</td>
                    </tr>
                    <tr className="border-b border-synapse-border/50">
                      <td className="py-3 text-synapse-text">Power Levels</td>
                      <td className="text-center py-3 text-synapse-text-muted">Low, Med</td>
                      <td className="text-center py-3 text-synapse-text-muted">All Levels</td>
                      <td className="text-center py-3 text-synapse-text-muted">All + Custom</td>
                    </tr>
                    <tr className="border-b border-synapse-border/50">
                      <td className="py-3 text-synapse-text">API Access</td>
                      <td className="text-center py-3 text-synapse-error">✗</td>
                      <td className="text-center py-3 text-synapse-success">✓</td>
                      <td className="text-center py-3 text-synapse-success">✓ Unlimited</td>
                    </tr>
                    <tr className="border-b border-synapse-border/50">
                      <td className="py-3 text-synapse-text">Support</td>
                      <td className="text-center py-3 text-synapse-text-muted">Email</td>
                      <td className="text-center py-3 text-synapse-text-muted">Priority</td>
                      <td className="text-center py-3 text-synapse-text-muted">Dedicated</td>
                    </tr>
                    <tr>
                      <td className="py-3 text-synapse-text">SLA</td>
                      <td className="text-center py-3 text-synapse-error">✗</td>
                      <td className="text-center py-3 text-synapse-error">✗</td>
                      <td className="text-center py-3 text-synapse-success">99.9%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Credits Tab */}
        {activeTab === 'credits' && (
          <div className="space-y-12">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-synapse-text-bright mb-4">
                Credit Packages
              </h2>
              <p className="text-lg text-synapse-text-muted">
                Need more credits? Purchase additional credit packs to supplement your monthly allowance.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {creditPacks.map((pack, index) => (
                <div
                  key={index}
                  className={`relative rounded-xl border p-6 transition-all duration-200 ${
                    pack.popular
                      ? 'border-synapse-primary bg-synapse-primary/5 scale-105 shadow-lg'
                      : 'border-synapse-border bg-synapse-card hover:border-synapse-primary/30'
                  }`}
                >
                  {pack.popular && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-synapse-primary text-synapse-primary-foreground px-3 py-1 rounded-full text-xs font-medium">
                      Best Value
                    </div>
                  )}

                  <div className="text-center mb-6">
                    <div className="w-16 h-16 bg-synapse-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                      <Zap className="h-8 w-8 text-synapse-primary" />
                    </div>
                    
                    <div className="text-2xl font-bold text-synapse-text-bright mb-1">
                      {pack.credits.toLocaleString()}
                      {pack.bonus > 0 && (
                        <span className="text-lg text-synapse-success ml-1">
                          +{pack.bonus}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-synapse-text-muted mb-2">Credits</div>
                    <div className="text-xs text-synapse-text-muted mb-4">
                      {pack.description}
                    </div>
                    {pack.bonus > 0 && (
                      <div className="text-xs text-synapse-success font-medium mb-4">
                        {pack.bonus} bonus credits included!
                      </div>
                    )}
                  </div>

                  <div className="text-center mb-6">
                    <div className="text-3xl font-bold text-synapse-primary mb-1">
                      ${pack.price}
                    </div>
                    <div className="text-xs text-synapse-text-muted">
                      ${(pack.price / (pack.credits + pack.bonus)).toFixed(3)} per credit
                    </div>
                  </div>

                  <button
                    onClick={() => handleCreditPurchase(pack)}
                    disabled={isLoading}
                    className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-200 disabled:opacity-50 flex items-center justify-center ${
                      pack.popular
                        ? 'bg-synapse-primary hover:bg-synapse-primary-hover text-synapse-primary-foreground'
                        : 'border border-synapse-border text-synapse-text hover:bg-synapse-hover'
                    }`}
                  >
                    {isLoading ? (
                      <>
                        <div className="spinner mr-2" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <CreditCard className="h-4 w-4 mr-2" />
                        Purchase Credits
                      </>
                    )}
                  </button>
                </div>
              ))}
            </div>

            {/* Credit Usage Tips */}
            <div className="bg-synapse-surface/50 border border-synapse-border rounded-xl p-8">
              <h3 className="text-xl font-semibold text-synapse-text-bright mb-6">
                Understanding Credit Usage
              </h3>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-synapse-text mb-3">Power Level Costs</h4>
                  <ul className="space-y-2 text-sm text-synapse-text-muted">
                    <li>• <strong>Low:</strong> 25 credits per prompt</li>
                    <li>• <strong>Medium:</strong> 50 credits per prompt</li>
                    <li>• <strong>High:</strong> 100 credits per prompt</li>
                    <li>• <strong>Pro:</strong> 200 credits per prompt</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium text-synapse-text mb-3">Usage Tips</h4>
                  <ul className="space-y-2 text-sm text-synapse-text-muted">
                    <li>• Credits never expire once purchased</li>
                    <li>• Use lower power levels for simple tasks</li>
                    <li>• Pro level for complex, critical prompts</li>
                    <li>• Monitor usage in your dashboard</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Enterprise Contact */}
        <div className="text-center mt-16 p-8 bg-synapse-surface/30 rounded-xl border border-synapse-border">
          <h3 className="text-2xl font-bold text-synapse-text-bright mb-4">
            Need a Custom Solution?
          </h3>
          <p className="text-synapse-text-muted mb-6 max-w-2xl mx-auto">
            We offer custom pricing for high-volume users, enterprise integrations, and specialized requirements. 
            Let's discuss how Synapse can fit your organization's needs.
          </p>
          <button
            onClick={() => window.open('mailto:sales@synapse.com?subject=Custom Plan Inquiry', '_blank')}
            className="bg-synapse-primary hover:bg-synapse-primary-hover text-synapse-primary-foreground font-medium py-3 px-6 rounded-lg transition-all duration-200"
          >
            Contact Sales Team
          </button>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPage;
