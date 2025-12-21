import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Privacy Policy | Hostamar',
  description: 'Learn about how Hostamar collects, uses, and protects your personal data.',
}

export default function PrivacyPolicy() {
  const currentDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })

  return (
    <div className="max-w-4xl mx-auto px-4 py-16 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 pb-8">
        <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight sm:text-5xl mb-4">
          Privacy Policy
        </h1>
        <p className="text-lg text-gray-600">
          Last updated: {currentDate}
        </p>
      </div>

      {/* Content */}
      <div className="prose prose-blue max-w-none text-gray-700">
        <p className="lead text-xl text-gray-600 mb-8">
          At Hostamar, we take your privacy seriously. This policy describes how we collect, use, and handle your personal information when you use our websites, software, and services ("Services").
        </p>

        <section className="mb-10">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Data Collection</h2>
          <p className="mb-4">
            We collect information you provide directly to us, such as when you create an account, purchase hosting services, use our AI tools, or communicate with us. This may include:
          </p>
          <ul className="list-disc pl-6 space-y-2 mb-4">
            <li><strong>Account Information:</strong> Name, email address, password, and contact details.</li>
            <li><strong>Payment Data:</strong> Billing address and payment method details (processed by secure third-party processors).</li>
            <li><strong>Usage Data:</strong> Server logs, device information, and interaction data from your use of our platform.</li>
            <li><strong>Content:</strong> Files, scripts, and media you upload to our hosting services or generate via our AI tools.</li>
          </ul>
        </section>

        <section className="mb-10">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">2. How We Use Your Data</h2>
          <p className="mb-4">
            We use the information we collect to provide, maintain, and improve our Services. Specifically, we use your data to:
          </p>
          <ul className="list-disc pl-6 space-y-2 mb-4">
            <li>Process transactions and manage your cloud hosting resources.</li>
            <li>Provide customer support and technical assistance.</li>
            <li>Send you technical notices, updates, security alerts, and administrative messages.</li>
            <li>Detect and prevent fraud, abuse, and security incidents.</li>
            <li>Improve our AI models and algorithms (only using anonymized, non-personal data where applicable).</li>
          </ul>
        </section>

        <section className="mb-10">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Data Security</h2>
          <p className="mb-4">
            We implement robust security measures to protect your personal information. These include encryption of data in transit and at rest, strict access controls, and regular security audits. However, no internet transmission is completely secure, and we cannot guarantee the absolute security of your data.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">4. User Rights</h2>
          <p className="mb-4">
            Depending on your location, you may have specific rights regarding your personal data, including the right to:
          </p>
          <ul className="list-disc pl-6 space-y-2 mb-4">
            <li>Access the personal data we hold about you.</li>
            <li>Request correction of inaccurate data.</li>
            <li>Request deletion of your data ("Right to be Forgotten").</li>
            <li>Opt-out of marketing communications at any time.</li>
          </ul>
        </section>

        <section className="mb-10">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Cookies and Tracking</h2>
          <p className="mb-4">
            We use cookies and similar technologies to track user activity on our Service and hold certain information. Cookies help us understand how you use our site, remember your preferences, and improve your experience. You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Policy Updates</h2>
          <p className="mb-4">
            We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last updated" date. We advise you to review this policy periodically for any changes.
          </p>
        </section>

        <section className="mb-10 border-t border-gray-200 pt-10 mt-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Contact Information</h2>
          <p className="mb-4">
            If you have any questions about this Privacy Policy, please contact us:
          </p>
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-100">
            <p className="font-semibold text-gray-900">Hostamar Privacy Team</p>
            <p className="text-gray-600 mt-1">Email: privacy@hostamar.com</p>
            <p className="text-gray-600">Address: 123 Cloud Street, Tech City, TC 90210</p>
          </div>
        </section>
      </div>
    </div>
  )
}
