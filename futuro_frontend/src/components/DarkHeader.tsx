import { Search, Heart } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';

export function DarkHeader() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-gray-800 bg-black/95 backdrop-blur-md">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-8">
            <a href="/" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded bg-lime-400">
                <span className="text-black">DH</span>
              </div>
              <span className="text-white">DesignHub</span>
            </a>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-6">
              <a href="#explore" className="text-gray-300 hover:text-white transition-colors">
                Explore
              </a>
              <a href="#help" className="text-gray-300 hover:text-white transition-colors">
                Help
              </a>
              <a href="#pricing" className="text-gray-300 hover:text-white transition-colors">
                Pricing
              </a>
            </nav>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-4">
            <button className="text-gray-400 hover:text-white transition-colors">
              <Search className="h-5 w-5" />
            </button>
            
            <button className="text-gray-400 hover:text-white transition-colors">
              <Heart className="h-5 w-5" />
            </button>
            
            <Avatar className="h-8 w-8">
              <AvatarImage src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop" />
              <AvatarFallback>DH</AvatarFallback>
            </Avatar>
          </div>
        </div>
      </div>
    </header>
  );
}
