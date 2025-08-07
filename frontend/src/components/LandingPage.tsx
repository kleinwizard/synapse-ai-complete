import { useState } from 'react';
import { ArrowRight, Sparkles, Zap, Clock, CheckCircle, Code, Target, Lightbulb } from 'lucide-react';

interface LandingPageProps {
  onGetStarted: () => void;
}

const LandingPage = ({ onGetStarted }: LandingPageProps) => {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Lightbulb },
    { id: 'demo', label: 'Live Demo', icon: Code },
    { id: 'features', label: 'Features', icon: Target },
    { id: 'pricing', label: 'Pricing', icon: Zap },
  ];

  // Extended example prompt (2500+ words)
  const longExamplePrompt = `# Advanced Marketing Email Campaign Strategy & Execution Framework

## Executive Summary & Strategic Positioning

You are a senior marketing strategist and copywriting expert with 15+ years of experience in crafting high-conversion email marketing campaigns for Fortune 500 companies across diverse industries including SaaS, e-commerce, fintech, healthcare, and B2B services. Your expertise encompasses behavioral psychology, conversion rate optimization, A/B testing methodologies, marketing automation, customer journey mapping, and data-driven decision making.

Your comprehensive knowledge includes:
- Advanced email marketing platforms (HubSpot, Marketo, Pardot, Mailchimp, Klaviyo)
- Customer segmentation and persona development
- Lifecycle marketing and retention strategies
- Cross-channel marketing integration
- Email deliverability optimization
- GDPR and CAN-SPAM compliance
- Marketing analytics and attribution modeling

## Campaign Objective & Business Context

### Primary Goal Definition
Create a sophisticated, multi-touchpoint email marketing campaign designed to drive qualified lead generation and nurture prospects through a carefully orchestrated sales funnel. The campaign must achieve the following measurable outcomes:

- Increase email open rates by 35% above industry benchmark
- Achieve click-through rates exceeding 8.5%
- Generate qualified leads with a cost-per-acquisition 40% below current performance
- Drive conversion rates of 12%+ from email to desired action
- Maintain list health with unsubscribe rates below 2%

### Target Audience Analysis & Segmentation

#### Primary Persona: "The Strategic Decision Maker"
- **Demographics**: Directors, VPs, C-level executives aged 35-55
- **Psychographics**: Results-oriented, time-constrained, data-driven decision makers
- **Pain Points**: Inefficient processes, budget constraints, competitive pressure, scalability challenges
- **Preferred Communication**: Direct, value-focused, backed by credible data and social proof
- **Decision-Making Process**: Collaborative, requires ROI justification, seeks vendor validation

#### Secondary Persona: "The Tactical Implementer"
- **Demographics**: Managers, specialists, team leads aged 28-45
- **Psychographics**: Detail-oriented, process-focused, seeking efficiency improvements
- **Pain Points**: Resource limitations, tool integration challenges, performance measurement
- **Preferred Communication**: Practical, solution-oriented, with clear implementation guidance
- **Decision-Making Process**: Influenced by peer recommendations, seeks proven methodologies

### Competitive Landscape & Positioning Strategy

Analyze and differentiate from key competitors by emphasizing unique value propositions:
- Superior technology capabilities and integration possibilities
- Exceptional customer support and onboarding experience
- Proven track record with quantifiable success metrics
- Industry-specific expertise and tailored solutions
- Cost-effectiveness compared to alternative solutions

## Email Campaign Architecture & Structure

### Campaign Flow Design (7-Touch Sequence)

#### Email 1: Welcome & Value Introduction (Day 0)
**Subject Line Strategy:**
- Primary: "Welcome to [Company] - Your success journey starts now"
- A/B Variant: "3 immediate wins waiting for you inside"
- Mobile Optimization: 30-35 characters for optimal display

**Content Framework:**
- Personal welcome from CEO/founder (builds authority and trust)
- Clear value proposition statement with benefit-focused language
- Immediate access to valuable resource (whitepaper, toolkit, checklist)
- Set expectations for upcoming content and communication frequency
- Strong secondary CTA for scheduling consultation/demo

#### Email 2: Educational Content & Problem Agitation (Day 3)
**Subject Line Strategy:**
- Primary: "The hidden cost of [specific pain point] - shocking statistics inside"
- A/B Variant: "Why 73% of [target audience] struggle with [problem]"

**Content Framework:**
- Industry-specific statistics and research findings
- Case study highlighting common challenges and consequences
- Introduction of potential solutions without overt selling
- Valuable, actionable tips for immediate implementation
- CTA to access additional educational resources

#### Email 3: Social Proof & Authority Building (Day 7)
**Subject Line Strategy:**
- Primary: "How [recognizable client] achieved [specific result] in [timeframe]"
- A/B Variant: "[Number] companies just like yours are seeing [benefit]"

**Content Framework:**
- Detailed customer success story with quantifiable results
- Before/after scenario showcasing transformation
- Client testimonial with photo and company details
- Industry awards, certifications, or recognition
- CTA to view additional case studies or client testimonials

#### Email 4: Product/Service Introduction (Day 12)
**Subject Line Strategy:**
- Primary: "Introducing the solution [client name] used to achieve [result]"
- A/B Variant: "The [product/service] behind [impressive statistic/result]"

**Content Framework:**
- Product overview with clear benefit statements
- Key features that address previously mentioned pain points
- Unique differentiators and competitive advantages
- Implementation process and expected timeline
- Primary CTA for product demo or free trial

#### Email 5: Urgency & Scarcity (Day 18)
**Subject Line Strategy:**
- Primary: "Limited spots remaining - don't miss out [first name]"
- A/B Variant: "Only [number] days left to claim your [benefit/offer]"

**Content Framework:**
- Time-sensitive offer with clear deadline
- Bonus incentives for quick decision-making
- Risk reversal through guarantee or trial period
- FOMO-inducing language while maintaining professionalism
- Strong primary CTA with urgency indicators

#### Email 6: Objection Handling & FAQ (Day 23)
**Subject Line Strategy:**
- Primary: "Addressing your concerns about [product/service]"
- A/B Variant: "The honest answers to your [product] questions"

**Content Framework:**
- Address common objections and concerns proactively
- Detailed FAQ section with honest, transparent answers
- Additional social proof and risk mitigation strategies
- Comparison with alternative solutions
- CTA to speak with specialist for personalized consultation

#### Email 7: Final Call & Alternative Offers (Day 28)
**Subject Line Strategy:**
- Primary: "Last chance - plus a special alternative for you"
- A/B Variant: "If [primary offer] isn't right, try this instead"

**Content Framework:**
- Final opportunity messaging with deadline reinforcement
- Alternative lower-commitment offers (consultation, audit, resource)
- Clear value restatement and benefit summary
- Multiple CTA options catering to different commitment levels
- Option to update preferences rather than unsubscribe

### Technical Implementation Requirements

#### Email Template Design Specifications
- Mobile-first responsive design with 600px maximum width
- Single-column layout for optimal mobile readability
- Brand-consistent color palette and typography
- Accessible design following WCAG 2.1 guidelines
- Loading speed optimization under 15KB per email

#### Personalization & Dynamic Content Strategy
- First name personalization throughout subject lines and content
- Company name integration where available
- Industry-specific pain points and case studies
- Geographic customization for relevant examples
- Behavioral triggers based on previous engagement

#### A/B Testing Framework
- Subject line variations for each email (minimum 2 variants)
- Send time optimization (testing 9 AM, 2 PM, 6 PM)
- CTA button text and color variations
- Email length testing (concise vs. detailed formats)
- Sender name testing (individual vs. company)

### Deliverability & Compliance Optimization

#### Technical Setup Requirements
- SPF, DKIM, and DMARC authentication configuration
- Dedicated IP address with proper warming schedule
- List hygiene protocols and bounce management
- Spam filter testing and optimization
- Unsubscribe link compliance and processing

#### Content Compliance Guidelines
- CAN-SPAM Act compliance verification
- GDPR consent management and documentation
- Clear sender identification and contact information
- Honest subject lines without deceptive practices
- Proper unsubscribe mechanisms and processing

### Performance Measurement & Analytics

#### Key Performance Indicators (KPIs)
- Open rates (target: 25%+ for B2B, 20%+ for B2C)
- Click-through rates (target: 3%+ for B2B, 2.5%+ for B2C)
- Conversion rates (target: 10%+ from email to landing page)
- List growth rate and subscriber acquisition cost
- Revenue attribution and customer lifetime value

#### Advanced Analytics Implementation
- UTM parameter strategy for accurate tracking
- Conversion funnel analysis from email to purchase
- Cohort analysis for long-term engagement trends
- Heat mapping for email content optimization
- Integration with CRM for sales attribution

### Risk Management & Contingency Planning

#### List Management Best Practices
- Regular list cleaning and engagement-based segmentation
- Re-engagement campaigns for inactive subscribers
- Preference center for subscriber control and retention
- Sunset policies for chronically unengaged contacts
- Data backup and recovery protocols

#### Campaign Optimization Strategies
- Continuous A/B testing for performance improvement
- Feedback loop implementation for subscriber insights
- Competitive analysis and benchmarking
- Seasonal and market trend adaptation
- Emergency communication protocols for crisis management

## Advanced Psychological Triggers & Persuasion Techniques

### Behavioral Psychology Applications
- Reciprocity principle through valuable free content
- Social proof integration throughout customer journey
- Authority building through expert positioning and credentials
- Scarcity and urgency without manipulation
- Consistency principle through commitment and follow-through

### Emotional Engagement Strategies
- Storytelling techniques for memorable messaging
- Empathy building through shared challenges recognition
- Achievement visualization and success imagery
- Fear of missing out (FOMO) balanced with positive motivation
- Community building and belonging enhancement

This comprehensive framework ensures maximum engagement, conversion optimization, and long-term relationship building while maintaining ethical marketing practices and regulatory compliance. The strategy integrates cutting-edge marketing techniques with proven psychological principles to deliver exceptional results for your email marketing campaigns.`;

  return (
    <div className="min-h-screen bg-gradient-hero">
      {/* Navigation Tabs */}
      <nav className="border-b border-synapse-border/50 bg-synapse-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold text-synapse-primary py-4">
              Synapse
            </div>
            
            <div className="flex space-x-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center px-6 py-4 text-sm font-medium transition-all duration-200 border-b-2 ${
                      activeTab === tab.id
                        ? 'text-synapse-primary border-synapse-primary'
                        : 'text-synapse-text-muted border-transparent hover:text-synapse-text hover:border-synapse-border'
                    }`}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            <button 
              onClick={onGetStarted}
              className="btn-hero text-sm px-6 py-2"
            >
              Get Started Free
            </button>
          </div>
        </div>
      </nav>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-20">
            {/* Hero Section */}
            <section className="text-center py-20">
              <h1 className="text-6xl font-bold text-synapse-text-bright mb-6 leading-tight">
                From Simple Idea to<br />
                <span className="bg-gradient-primary bg-clip-text text-transparent">
                  Expert Prompt
                </span>{" "}
                in Seconds
              </h1>
              <p className="text-xl text-synapse-text-muted max-w-2xl mx-auto mb-12">
                Transform your basic concepts into powerful, structured prompts that unlock the full potential of AI. 
                No expertise required.
              </p>
              <button 
                onClick={onGetStarted}
                className="btn-hero group"
              >
                Get Started for Free
                <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
              </button>
            </section>

            {/* Value Proposition */}
            <section className="grid md:grid-cols-3 gap-8">
              <div className="synapse-card text-center">
                <div className="w-16 h-16 bg-synapse-primary/10 rounded-xl flex items-center justify-center mx-auto mb-6">
                  <Sparkles className="h-8 w-8 text-synapse-primary" />
                </div>
                <h3 className="text-xl font-semibold text-synapse-text-bright mb-4">
                  Instant Enhancement
                </h3>
                <p className="text-synapse-text-muted">
                  Upload any basic prompt and watch as our AI transforms it into a comprehensive, expert-level instruction set.
                </p>
              </div>

              <div className="synapse-card text-center">
                <div className="w-16 h-16 bg-synapse-primary/10 rounded-xl flex items-center justify-center mx-auto mb-6">
                  <Zap className="h-8 w-8 text-synapse-primary" />
                </div>
                <h3 className="text-xl font-semibold text-synapse-text-bright mb-4">
                  Power Level Control
                </h3>
                <p className="text-synapse-text-muted">
                  Choose your enhancement level from Low to Pro based on complexity needs and credit budget.
                </p>
              </div>

              <div className="synapse-card text-center">
                <div className="w-16 h-16 bg-synapse-primary/10 rounded-xl flex items-center justify-center mx-auto mb-6">
                  <Clock className="h-8 w-8 text-synapse-primary" />
                </div>
                <h3 className="text-xl font-semibold text-synapse-text-bright mb-4">
                  Production Ready
                </h3>
                <p className="text-synapse-text-muted">
                  Get professional-grade prompts ready for immediate use in your workflows and applications.
                </p>
              </div>
            </section>
          </div>
        )}

        {activeTab === 'demo' && (
          <div className="space-y-12">
            <div className="text-center">
              <h2 className="text-4xl font-bold text-synapse-text-bright mb-4">
                See the Transformation
              </h2>
              <p className="text-lg text-synapse-text-muted">
                Watch how Synapse transforms simple ideas into comprehensive expert prompts
              </p>
            </div>
            
            <div className="grid lg:grid-cols-2 gap-12 items-start">
              {/* Input Side */}
              <div className="space-y-4">
                <div className="text-sm font-medium text-synapse-text-muted uppercase tracking-wide">
                  Your Simple Input
                </div>
                <div className="synapse-card">
                  <textarea
                    value="Help me write a marketing email"
                    readOnly
                    className="w-full bg-transparent text-synapse-text resize-none border-none outline-none text-lg"
                    rows={3}
                  />
                </div>
              </div>

              {/* Output Side */}
              <div className="space-y-4">
                <div className="text-sm font-medium text-synapse-text-muted uppercase tracking-wide">
                  Expert-Level Output (2500+ words)
                </div>
                <div className="synapse-card bg-synapse-background max-h-96 overflow-auto">
                  <pre className="text-xs text-synapse-text leading-relaxed whitespace-pre-wrap">
                    {longExamplePrompt}
                  </pre>
                </div>
              </div>
            </div>

            <div className="text-center">
              <button 
                onClick={onGetStarted}
                className="btn-hero group"
              >
                Try It Yourself
                <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
              </button>
            </div>
          </div>
        )}
        {activeTab === 'features' && (
          <div className="space-y-16">
            <div className="text-center">
              <h2 className="text-4xl font-bold text-synapse-text-bright mb-4">
                Powerful Features for Every Use Case
              </h2>
              <p className="text-lg text-synapse-text-muted">
                Everything you need to create professional-grade prompts
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              <div className="synapse-card">
                <div className="w-12 h-12 bg-synapse-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <Sparkles className="h-6 w-6 text-synapse-primary" />
                </div>
                <h3 className="text-lg font-semibold text-synapse-text-bright mb-3">
                  AI-Powered Enhancement
                </h3>
                <p className="text-synapse-text-muted text-sm">
                  Advanced AI analyzes your input and applies expert-level prompt engineering techniques automatically.
                </p>
              </div>

              <div className="synapse-card">
                <div className="w-12 h-12 bg-synapse-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <Zap className="h-6 w-6 text-synapse-primary" />
                </div>
                <h3 className="text-lg font-semibold text-synapse-text-bright mb-3">
                  Multiple Power Levels
                </h3>
                <p className="text-synapse-text-muted text-sm">
                  Choose from Low, Med, High, or Pro levels to match your complexity needs and credit budget.
                </p>
              </div>

              <div className="synapse-card">
                <div className="w-12 h-12 bg-synapse-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <Clock className="h-6 w-6 text-synapse-primary" />
                </div>
                <h3 className="text-lg font-semibold text-synapse-text-bright mb-3">
                  Instant Results
                </h3>
                <p className="text-synapse-text-muted text-sm">
                  Get your enhanced prompts in seconds, not hours. Perfect for rapid iteration and testing.
                </p>
              </div>

              <div className="synapse-card">
                <div className="w-12 h-12 bg-synapse-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <Code className="h-6 w-6 text-synapse-primary" />
                </div>
                <h3 className="text-lg font-semibold text-synapse-text-bright mb-3">
                  API Access
                </h3>
                <p className="text-synapse-text-muted text-sm">
                  Integrate Synapse into your existing workflows with our comprehensive REST API.
                </p>
              </div>

              <div className="synapse-card">
                <div className="w-12 h-12 bg-synapse-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <Target className="h-6 w-6 text-synapse-primary" />
                </div>
                <h3 className="text-lg font-semibold text-synapse-text-bright mb-3">
                  Industry Templates
                </h3>
                <p className="text-synapse-text-muted text-sm">
                  Pre-built templates for marketing, development, research, and other common use cases.
                </p>
              </div>

              <div className="synapse-card">
                <div className="w-12 h-12 bg-synapse-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <CheckCircle className="h-6 w-6 text-synapse-primary" />
                </div>
                <h3 className="text-lg font-semibold text-synapse-text-bright mb-3">
                  Quality Assurance
                </h3>
                <p className="text-synapse-text-muted text-sm">
                  Every prompt is validated for clarity, structure, and effectiveness before delivery.
                </p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'pricing' && (
          <div className="space-y-16">
            <div className="text-center">
              <h2 className="text-4xl font-bold text-synapse-text-bright mb-4">
                Simple, Transparent Pricing
              </h2>
              <p className="text-lg text-synapse-text-muted">
                Start free and scale as you grow. No hidden fees, no surprises.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              <div className="pricing-card">
                <h3 className="text-xl font-semibold text-synapse-text-bright mb-2">Free</h3>
                <div className="text-3xl font-bold text-synapse-primary mb-4">$0</div>
                <div className="text-sm text-synapse-text-muted mb-6">Perfect for trying out Synapse</div>
                <ul className="space-y-3 text-sm text-synapse-text-muted mb-8">
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    100 credits/month
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    Basic power levels (Low, Med)
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    Community support
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    Basic templates
                  </li>
                </ul>
                <button onClick={onGetStarted} className="w-full border border-synapse-border text-synapse-text hover:bg-synapse-hover font-medium py-3 px-4 rounded-lg transition-all duration-200">
                  Get Started Free
                </button>
              </div>

              <div className="pricing-card current relative">
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-synapse-primary text-synapse-primary-foreground px-3 py-1 rounded-full text-xs font-medium">
                  Most Popular
                </div>
                <h3 className="text-xl font-semibold text-synapse-text-bright mb-2">Pro</h3>
                <div className="text-3xl font-bold text-synapse-primary mb-4">$29</div>
                <div className="text-sm text-synapse-text-muted mb-6">For professionals and teams</div>
                <ul className="space-y-3 text-sm text-synapse-text-muted mb-8">
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    2,000 credits/month
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    All power levels (Low, Med, High, Pro)
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    Priority support
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    API access
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    Advanced templates
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    Export functionality
                  </li>
                </ul>
                <button onClick={onGetStarted} className="w-full bg-synapse-primary hover:bg-synapse-primary-hover text-synapse-primary-foreground font-medium py-3 px-4 rounded-lg transition-all duration-200">
                  Start Pro Trial
                </button>
              </div>

              <div className="pricing-card">
                <h3 className="text-xl font-semibold text-synapse-text-bright mb-2">Enterprise</h3>
                <div className="text-3xl font-bold text-synapse-primary mb-4">Custom</div>
                <div className="text-sm text-synapse-text-muted mb-6">For large organizations</div>
                <ul className="space-y-3 text-sm text-synapse-text-muted mb-8">
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    Unlimited credits
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    Custom power levels
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    Dedicated support manager
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    Custom integrations
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    Team collaboration
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    Advanced analytics
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-synapse-success mr-2" />
                    SLA guarantee
                  </li>
                </ul>
                <button className="w-full border border-synapse-border text-synapse-text hover:bg-synapse-hover font-medium py-3 px-4 rounded-lg transition-all duration-200">
                  Contact Sales
                </button>
              </div>
            </div>

            <div className="text-center">
              <p className="text-sm text-synapse-text-muted mb-4">
                All plans include SSL security, 99.9% uptime guarantee, and data export capabilities.
              </p>
              <button 
                onClick={onGetStarted}
                className="btn-hero group"
              >
                Start Your Free Trial
                <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="border-t border-synapse-border bg-synapse-surface/30 mt-20">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="text-2xl font-bold text-synapse-primary mb-4 md:mb-0">
              Synapse
            </div>
            <div className="flex space-x-8 text-sm text-synapse-text-muted">
              <a href="/privacy" className="hover:text-synapse-text transition-colors">Privacy</a>
              <a href="/terms" className="hover:text-synapse-text transition-colors">Terms</a>
              <a href="#" className="hover:text-synapse-text transition-colors">Support</a>
              <a href="#" className="hover:text-synapse-text transition-colors">API Docs</a>
            </div>
          </div>
          <div className="text-center text-sm text-synapse-text-muted mt-8">
            © 2024 Synapse. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
