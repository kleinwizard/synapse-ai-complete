const Terms = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Terms of Service</h1>
          
          <div className="prose prose-gray max-w-none">
            <p className="text-lg text-gray-600 mb-6">
              Last updated: [Date]
            </p>
            
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">1. Acceptance of Terms</h2>
              <p className="text-gray-700 mb-4">
                By accessing and using Synapse AI, you accept and agree to be bound by the terms and provision of this agreement.
              </p>
            </section>
            
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">2. Use License</h2>
              <p className="text-gray-700 mb-4">
                Permission is granted to temporarily use Synapse AI for personal, non-commercial transitory viewing only.
              </p>
            </section>
            
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">3. Disclaimer</h2>
              <p className="text-gray-700 mb-4">
                The materials on Synapse AI are provided on an 'as is' basis. Synapse AI makes no warranties, expressed or implied.
              </p>
            </section>
            
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">4. Contact Information</h2>
              <p className="text-gray-700">
                If you have any questions about these Terms of Service, please contact us at support@synapse-ai.com.
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Terms;
