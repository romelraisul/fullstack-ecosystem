import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'About Us - Hostamar',
  description: 'Learn about our mission to revolutionize business growth with AI.',
}

export default function AboutPage() {
  return (
    <div className="container mx-auto px-4 py-16 max-w-4xl">
      <h1 className="text-4xl font-bold mb-8 text-center text-gray-900">About Hostamar</h1>
      
      <div className="prose prose-lg mx-auto text-gray-600">
        <p>
          At Hostamar, we believe that powerful technology should be accessible to everyone. 
          Founded in 2024, our mission is to bridge the gap between reliable cloud infrastructure 
          and cutting-edge AI marketing tools.
        </p>
        
        <h2 className="text-2xl font-bold text-gray-800 mt-8 mb-4">Our Vision</h2>
        <p>
          We envision a world where any entrepreneur, regardless of technical skill, can launch 
          a business online and instantly start marketing it to the world. We combine high-performance 
          VPS hosting with an autonomous AI video generation engine to make this possible.
        </p>

        <h2 className="text-2xl font-bold text-gray-800 mt-8 mb-4">Why We Are Different</h2>
        <ul className="list-disc pl-6 space-y-2">
          <li><strong>Integrated Ecosystem:</strong> No need to juggle hosting providers and marketing agencies.</li>
          <li><strong>AI-First Approach:</strong> Our tools don't just assist; they automate.</li>
          <li><strong>Local Focus, Global Standards:</strong> Optimized for the South Asian market with world-class infrastructure.</li>
        </ul>
      </div>
    </div>
  )
}
