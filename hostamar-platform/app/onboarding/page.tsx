'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Check } from 'lucide-react'

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [data, setData] = useState({
    businessName: '',
    industry: '',
    goal: '',
  })

  const handleNext = () => setStep(step + 1)
  const handleBack = () => setStep(step - 1)
  
  const handleFinish = async () => {
    // Submit onboarding data logic here
    // await updateProfile(data)
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full overflow-hidden">
        {/* Progress Bar */}
        <div className="bg-gray-100 h-2 w-full">
          <div 
            className="h-full bg-blue-600 transition-all duration-300" 
            style={{ width: `${(step / 3) * 100}%` }}
          />
        </div>

        <div className="p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Welcome to Hostamar!</h2>
            <p className="text-gray-500 text-sm mt-1">Let's set up your business profile.</p>
          </div>

          {/* Step 1: Business Info */}
          {step === 1 && (
            <div className="space-y-6">
              <Input 
                label="Business Name" 
                placeholder="e.g. Dhaka Electronics"
                value={data.businessName}
                onChange={e => setData({ ...data, businessName: e.target.value })}
                autoFocus
              />
              <div className="flex justify-end">
                <Button onClick={handleNext} disabled={!data.businessName}>Next</Button>
              </div>
            </div>
          )}

          {/* Step 2: Industry */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Select Industry</label>
                <div className="grid grid-cols-2 gap-3">
                  {['E-commerce', 'Education', 'Technology', 'Fashion', 'Food & Beverage', 'Other'].map(ind => (
                    <button
                      key={ind}
                      onClick={() => setData({ ...data, industry: ind })}
                      className={`p-3 text-sm border rounded-lg transition-all ${
                        data.industry === ind 
                          ? 'border-blue-600 bg-blue-50 text-blue-700 font-medium' 
                          : 'border-gray-200 hover:border-gray-300 text-gray-600'
                      }`}
                    >
                      {ind}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex justify-between">
                <Button variant="ghost" onClick={handleBack}>Back</Button>
                <Button onClick={handleNext} disabled={!data.industry}>Next</Button>
              </div>
            </div>
          )}

          {/* Step 3: Goals */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Primary Goal</label>
                <div className="space-y-3">
                  {[
                    { id: 'sales', label: 'Increase Sales', desc: 'Drive more revenue through marketing' },
                    { id: 'brand', label: 'Brand Awareness', desc: 'Get more people to know my brand' },
                    { id: 'hosting', label: 'Reliable Hosting', desc: 'Secure and fast website hosting' },
                  ].map(item => (
                    <button
                      key={item.id}
                      onClick={() => setData({ ...data, goal: item.id })}
                      className={`w-full p-4 text-left border rounded-xl transition-all flex items-start gap-3 ${
                        data.goal === item.id 
                          ? 'border-blue-600 bg-blue-50 ring-1 ring-blue-600' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className={`mt-0.5 w-5 h-5 rounded-full border flex items-center justify-center ${
                        data.goal === item.id ? 'border-blue-600 bg-blue-600' : 'border-gray-300'
                      }`}>
                        {data.goal === item.id && <Check className="w-3 h-3 text-white" />}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">{item.label}</div>
                        <div className="text-sm text-gray-500">{item.desc}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex justify-between">
                <Button variant="ghost" onClick={handleBack}>Back</Button>
                <Button onClick={handleFinish} disabled={!data.goal}>Finish Setup</Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
