import { Zap, Code2, Smartphone, Palette, Lock, Rocket } from 'lucide-react';

const features = [
  {
    icon: Zap,
    title: 'Lightning Fast',
    description: 'Optimized components built for performance and speed.'
  },
  {
    icon: Code2,
    title: 'Developer Friendly',
    description: 'Clean, semantic code that\'s easy to understand and customize.'
  },
  {
    icon: Smartphone,
    title: 'Fully Responsive',
    description: 'Every component works perfectly on all screen sizes.'
  },
  {
    icon: Palette,
    title: 'Highly Customizable',
    description: 'Easily adapt components to match your brand and design system.'
  },
  {
    icon: Lock,
    title: 'Accessible',
    description: 'Built with accessibility best practices and ARIA support.'
  },
  {
    icon: Rocket,
    title: 'Production Ready',
    description: 'Battle-tested components used by thousands of projects.'
  }
];

export function Features() {
  return (
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="mb-4">Why Choose UIWiki?</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Built with modern technologies and best practices to help you ship faster
          </p>
        </div>
        
        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div key={index} className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
                    <Icon className="h-6 w-6" />
                  </div>
                </div>
                <div>
                  <h3 className="mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-600">{feature.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
