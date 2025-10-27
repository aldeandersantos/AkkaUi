import { ArrowRight, Star } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-purple-50 via-white to-white py-20 md:py-32">
      {/* Background Gradient */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-100 via-transparent to-transparent opacity-60" />
      
      <div className="container mx-auto px-4 relative">
        <div className="max-w-4xl mx-auto text-center">
          {/* Badge */}
          <Badge variant="secondary" className="mb-6 gap-1 px-4 py-1.5">
            <Star className="h-3 w-3 fill-current" />
            <span>2000+ Components Available</span>
          </Badge>
          
          {/* Heading */}
          <h1 className="mb-6">
            Beautiful UI Components
            <br />
            <span className="bg-gradient-to-r from-purple-600 to-blue-500 bg-clip-text text-transparent">
              Copy. Paste. Done.
            </span>
          </h1>
          
          {/* Description */}
          <p className="mb-8 text-gray-600 max-w-2xl mx-auto">
            A comprehensive collection of beautifully designed, accessible, and customizable UI components. 
            Built with React, Tailwind CSS, and modern web standards.
          </p>
          
          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button size="lg" className="bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-700 hover:to-blue-600 gap-2">
              Browse Components
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button size="lg" variant="outline">
              View Documentation
            </Button>
          </div>
          
          {/* Stats */}
          <div className="mt-16 grid grid-cols-3 gap-8 max-w-2xl mx-auto">
            <div>
              <div className="text-purple-600 mb-1">2000+</div>
              <div className="text-gray-600 text-sm">Components</div>
            </div>
            <div>
              <div className="text-purple-600 mb-1">50k+</div>
              <div className="text-gray-600 text-sm">Developers</div>
            </div>
            <div>
              <div className="text-purple-600 mb-1">100%</div>
              <div className="text-gray-600 text-sm">Open Source</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
