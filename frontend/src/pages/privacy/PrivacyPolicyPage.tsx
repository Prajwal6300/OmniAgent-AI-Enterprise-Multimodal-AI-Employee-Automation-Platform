import React from 'react';

export default function PrivacyPolicyPage() {
  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-ink mb-6">Privacy Policy</h1>
      <div className="prose max-w-none">
        <p className="mb-6">
          <strong>Effective date:</strong> October 15, 2026
        </p>
        <p>
          <strong>OmniAgent AI</strong> operates the OmniAgent AI platform. This privacy policy discloses what personal information we collect and how we use it.
        </p>

        <h2 className="text-xl font-semibold text-ink mt-8">1. Information We Collect</h2>
        <h3 className="text-base font-medium text-ink mt-3">1.1 Account Information</h3>
        <ul className="list-disc list-inside mb-4">
          <li>Email address</li>
          <li>Full name</li>
          <li>Hashed password</li>
        </ul>

        <h3 className="text-base font-medium text-ink mt-3">1.2 Organization Information</h3>
        <ul className="list-disc list-inside mb-4">
          <li>Organization name</li>
          <li>Organization slug</li>
        </ul>

        <h2 className="text-xl font-semibold text-ink mt-8">2. How We Use Your Information</h2>
        <ul className="list-disc list-inside mb-4">
          <li>To provide and maintain the Service</li>
          <li>To notify you about changes to our Service</li>
          <li>To allow you to participate in interactive features of our Service when you choose to do so</li>
          <li>To provide customer support</li>
          <li>To analyze how our Service is used</li>
          <li>To detect, prevent, and address security and technical issues</li>
        </ul>

        <h2 className="text-xl font-semibold text-ink mt-8">3. Third-Party Sharing</h2>
        <p>
          We do not sell your personal information to third parties. We may share your information with:
        </p>
        <ul className="list-disc list-inside mb-4">
          <li>Service providers who work on our behalf</li>
          <li>Legal requirements fulfillment</li>
          <li>Business transfer in case of merger or acquisition</li>
        </ul>

        <h2 className="text-xl font-semibold text-ink mt-8">4. Data Retention</h2>
        <p>
          We retain your personal data until you delete your account or until the purpose for which it was collected has been fulfilled. Anonymous data may be retained indefinitely.
        </p>

        <h2 className="text-xl font-semibold text-ink mt-8">5. Your Rights</h2>
        <ul className="list-disc list-inside mb-4">
          <li>
            <strong>Access:</strong> You have the right to access and receive a copy of your personal data.
          </li>
          <li>
            <strong>Correction:</strong> You have the right to correct or update your personal data.
          </li>
          <li>
            <strong>Deletion:</strong> You have the right to request deletion of your personal data.
          </li>
          <li>
            <strong>Objection:</strong> You have the right to object to our processing of your personal data.
          </li>
          <li>
            <strong>Data portability:</strong> You have the right to data portability.
          </li>
        </ul>

<h2 className="text-xl font-semibold text-ink mt-8">6. Children Data</h2>
        <p>
          Our Service is not intended for anyone under the age of 18. We do not knowingly collect personal identifiable information from minors under 18. If you are a parent or guardian and you are aware that your child has provided us with personal data, please contact us immediately.
        </p>

        <h2 className="text-xl font-semibold text-ink mt-8">7. Changes to This Privacy Policy</h2>
        <p>
          We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the Effective date at the top of this page. You are advised to review this Privacy Policy periodically for any changes.
        </p>

        <p className="mt-6">
          <strong>Contact Us</strong>
        </p>
        <p>
          If you have any questions about this Privacy Policy, you can contact us at:
        </p>
        <a href={`mailto:${import.meta.env.VITE_CONTACT_EMAIL || "contact@omniagent.ai"}`} className="text-indigo-600 hover:text-indigo-500">
          {import.meta.env.VITE_CONTACT_EMAIL || "contact@omniagent.ai"}
        </a>
        <br />
        <br />
        <p>
          <strong>Draft - review by a qualified lawyer before launch.</strong>
        </p>
      </div>
    </div>
  );
}