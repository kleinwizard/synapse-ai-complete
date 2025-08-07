import { useState } from 'react';
import { Check, Zap, ArrowLeft, CreditCard } from 'lucide-react';

interface User {
  id: string;
  email: string;
  name: string;
}

interface BillingPageProps {
  user: User;
  onNavigate: (page: string) => void;
}

const plans = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    credits: 100,
    features: [
      '100 credits per month',
      'Basic power levels (Low, Med)',
      'Community support',
      'Basic prompt templates'
    ],
    isCurrent: true
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 29,
    credits: 2000,
    features: [
      '2,000 credits per month',
      'All power levels (Low, Med, High, Pro)',
      'Priority support',
      'Advanced prompt templates',
      'API access',
      'Export functionality'
    ],
    isPopular: true
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    credits: 'Unlimited',
    features: [
      'Unlimited credits',
      'Custom power levels',
      'Dedicated support manager',
      'Custom integrations',
      'Team collaboration',
      'Advanced analytics',
      'SLA guarantee'
    ]
  }
];

const creditPacks = [
  { credits: 500, price: 10, bonus: 0 },
  { credits: 1000, price: 18, bonus: 100 },
  { credits: 2500, price: 40, bonus: 300 }
];

const BillingPage = ({ user, onNavigate }: BillingPageProps) => {
  const [isProcessing, setIsProcessing] = useState(false);

  const handlePlanUpgrade = async (planId: string) => {
    if (planId === 'enterprise') {
      window.open('mailto:sales@synapse.com?subject=Enterprise Plan Inquiry', '_blank');
      return;
    }

    setIsProcessing(true);
    
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
          success_url: `${window.location.origin}/billing?success=true`,
          cancel_url: `${window.location.origin}/billing?canceled=true`
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
      setIsProcessing(false);
    }
  };

  const handleCreditPurchase = async (pack: typeof creditPacks[0]) => {
    setIsProcessing(true);
    
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
          success_url: `${window.location.origin}/billing?success=true`,
          cancel_url: `${window.location.origin}/billing?canceled=true`
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
      setIsProcessing(false);
    }
  };

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
            {user.name}
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-synapse-text-bright mb-2">
            Subscription & Billing
          </h1>
          <p className="text-synapse-text-muted">
            Manage your subscription plan and purchase additional credits
          </p>
        </div>

        {/* Subscription Plans */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-synapse-text-bright mb-6">
            Subscription Plans
          </h2>
          
          <div className="grid md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className={`pricing-card relative ${plan.isCurrent ? 'current' : ''}`}
              >
                {plan.isPopular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-synapse-primary text-synapse-primary-foreground px-3 py-1 rounded-full text-xs font-medium">
                    Most Popular
                  </div>
                )}
                
                {plan.isCurrent && (
                  <div className="absolute -top-3 right-4 bg-synapse-success text-white px-3 py-1 rounded-full text-xs font-medium">
                    Current Plan
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-xl font-semibold text-synapse-text-bright mb-2">
                    {plan.name}
                  </h3>
                  <div className="flex items-baseline">
                    <span className="text-3xl font-bold text-synapse-primary">
                      ${plan.price}
                    </span>
                    {typeof plan.price === 'number' && (
                      <span className="text-synapse-text-muted ml-1">/month</span>
                    )}
                  </div>
                  <div className="text-sm text-synapse-text-muted mt-1">
                    {typeof plan.credits === 'number' 
                      ? `${plan.credits.toLocaleString()} credits/month`
                      : plan.credits
                    }
                  </div>
                </div>

                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <Check className="h-4 w-4 text-synapse-success mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-synapse-text-muted">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => plan.id !== 'free' && handlePlanUpgrade(plan.id)}
                  disabled={plan.isCurrent || isProcessing}
                  className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-200 ${
                    plan.isCurrent
                      ? 'bg-synapse-surface text-synapse-text-muted cursor-not-allowed'
                      : plan.isPopular
                      ? 'bg-synapse-primary text-synapse-primary-foreground hover:bg-synapse-primary-hover'
                      : 'border border-synapse-border text-synapse-text hover:bg-synapse-hover'
                  }`}
                >
                  {isProcessing ? (
                    <div className="flex items-center justify-center">
                      <div className="spinner mr-2" />
                      Processing...
                    </div>
                  ) : plan.isCurrent ? (
                    'Current Plan'
                  ) : plan.id === 'enterprise' ? (
                    'Contact Sales'
                  ) : (
                    'Upgrade'
                  )}
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* Credit Top-Up */}
        <section>
          <div className="mb-6">
            <h2 className="text-2xl font-semibold text-synapse-text-bright mb-2">
              Need More Credits?
            </h2>
            <p className="text-synapse-text-muted">
              Purchase additional credit packs to supplement your monthly allowance
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {creditPacks.map((pack, index) => (
              <div key={index} className="synapse-card">
                <div className="text-center mb-6">
                  <div className="w-16 h-16 bg-synapse-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Zap className="h-8 w-8 text-synapse-primary" />
                  </div>
                  
                  <div className="text-2xl font-bold text-synapse-text-bright mb-1">
                    {pack.credits.toLocaleString()}
                    {pack.bonus > 0 && (
                      <span className="text-lg text-synapse-success">
                        {' '}+ {pack.bonus}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-synapse-text-muted mb-1">Credits</div>
                  {pack.bonus > 0 && (
                    <div className="text-xs text-synapse-success font-medium">
                      {pack.bonus} bonus credits included!
                    </div>
                  )}
                </div>

                <div className="text-center mb-6">
                  <div className="text-3xl font-bold text-synapse-primary">
                    ${pack.price}
                  </div>
                  <div className="text-sm text-synapse-text-muted">
                    ${(pack.price / pack.credits).toFixed(3)} per credit
                  </div>
                </div>

                <button
                  onClick={() => handleCreditPurchase(pack)}
                  disabled={isProcessing}
                  className="w-full bg-synapse-primary hover:bg-synapse-primary-hover text-synapse-primary-foreground font-medium py-3 px-4 rounded-lg transition-all duration-200 disabled:opacity-50 flex items-center justify-center"
                >
                  {isProcessing ? (
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

          <div className="mt-8 text-center">
            <p className="text-sm text-synapse-text-muted">
              Need a custom solution?{' '}
              <a href="#" className="text-synapse-primary hover:underline">
                Contact our sales team
              </a>{' '}
              for enterprise pricing and bulk credit packages.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
};

export default BillingPage;
