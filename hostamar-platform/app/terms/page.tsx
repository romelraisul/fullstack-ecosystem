
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms & Conditions - Hostamar',
  description: 'Terms and Conditions for Hostamar.com services',
};

export default function TermsPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-4xl font-bold mb-6">Terms and Conditions</h1>
      
      <p className="mb-4">
        Welcome to Hostamar! These terms and conditions outline the rules and regulations for the use of Hostamar's Website, located at https://hostamar.com.
      </p>

      <p className="mb-4">
        By accessing this website we assume you accept these terms and conditions. Do not continue to use Hostamar.com if you do not agree to take all of the terms and conditions stated on this page.
      </p>

      <h2 className="text-2xl font-bold mt-8 mb-4">1. Cookies</h2>
      <p className="mb-4">
        We employ the use of cookies. By accessing Hostamar.com, you agreed to use cookies in agreement with the Hostamar's Privacy Policy.
      </p>

      <h2 className="text-2xl font-bold mt-8 mb-4">2. License</h2>
      <p className="mb-4">
        Unless otherwise stated, Hostamar and/or its licensors own the intellectual property rights for all material on Hostamar.com. All intellectual property rights are reserved. You may access this from Hostamar.com for your own personal use subjected to restrictions set in these terms and conditions.
      </p>
      <ul className="list-disc pl-8 mb-4">
        <li>Republish material from Hostamar.com</li>
        <li>Sell, rent or sub-license material from Hostamar.com</li>
        <li>Reproduce, duplicate or copy material from Hostamar.com</li>
        <li>Redistribute content from Hostamar.com</li>
      </ul>

      <p className="mb-4">
        This Agreement shall begin on the date hereof.
      </p>

      <h2 className="text-2xl font-bold mt-8 mb-4">3. Your Privacy</h2>
      <p className="mb-4">
        Please read our Privacy Policy.
      </p>

      <h2 className="text-2xl font-bold mt-8 mb-4">4. Reservation of Rights</h2>
      <p className="mb-4">
        We reserve the right to request that you remove all links or any particular link to our Website. You approve to immediately remove all links to our Website upon request. We also reserve the right to amen these terms and conditions and it’s linking policy at any time. By continuously linking to our Website, you agree to be bound to and follow these linking terms and conditions.
      </p>
      
      <p className="mt-8 text-gray-600 text-sm">
        Last updated: December 14, 2025
      </p>
    </div>
  );
}
