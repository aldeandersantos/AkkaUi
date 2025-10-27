import { Search } from 'lucide-react';
import { Input } from './ui/input';
import { Badge } from './ui/badge';

const categories = [
  'Ecommerce', 'Website', 'Saas', 'Education', 'Agency', 'Wireframe', 'Dashboard', 'App', 'Landing', 'Marketplace'
];

export function DarkHero() {
  return (
    <section className="relative overflow-hidden bg-black pt-20 pb-16">
      {/* Background decorative elements */}
      <div className="absolute top-0 left-0 w-64 h-64 bg-gray-800 rounded-full blur-3xl opacity-20" />
      <div className="absolute top-0 right-0 w-64 h-64 bg-gray-800 rounded-full blur-3xl opacity-20" />
      
      <div className="container mx-auto px-4 relative">
        <div className="max-w-3xl mx-auto text-center">
          {/* Heading */}
          <h1 className="mb-6 text-white">
            Ready-to-Use Figma Designs for
            <br />
            <span className="text-gray-400">a Faster Workflow</span>
          </h1>
          
          {/* Search Bar */}
          <div className="mb-6 relative max-w-xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500" />
            <Input
              type="search"
              placeholder="Search..."
              className="pl-12 h-12 bg-gray-900 border-gray-800 text-white placeholder:text-gray-500 focus:border-gray-700"
            />
          </div>
          
          {/* Category Tags */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            {categories.map((category, index) => (
              <Badge 
                key={index}
                variant="secondary" 
                className="bg-gray-900 text-gray-300 hover:bg-gray-800 border border-gray-800 cursor-pointer"
              >
                {category}
              </Badge>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
