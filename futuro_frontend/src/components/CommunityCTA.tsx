import { ArrowRight } from 'lucide-react';
import { Input } from './ui/input';
import { Card } from './ui/card';

export function CommunityCTA() {
  return (
    <section className="bg-black py-16">
      <div className="container mx-auto px-4">
        <Card className="bg-gradient-to-br from-gray-900 to-gray-800 border-gray-700 max-w-4xl mx-auto">
          <div className="p-12 text-center">
            <h2 className="text-white mb-4">
              Join our community <span className="text-gray-400">and</span>
              <br />
              claim free products
            </h2>
            
            <p className="text-gray-400 mb-8 max-w-2xl mx-auto">
              Explore + download + get 28 FREE products templates
              <br />
              first thing - one or your first or as all are
            </p>
            
            {/* Email Input */}
            <div className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <Input
                type="email"
                placeholder="Type your email..."
                className="flex-1 bg-gray-800 border-gray-700 text-white placeholder:text-gray-500 h-12"
              />
              <button className="px-8 py-3 bg-lime-400 hover:bg-lime-500 text-black rounded-md transition-colors inline-flex items-center justify-center gap-2 whitespace-nowrap h-12">
                <span>Subscribe</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </Card>
      </div>
    </section>
  );
}
