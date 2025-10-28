import { Search, Menu, Github } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/80 backdrop-blur-md">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-8">
            <a href="/" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-purple-600 to-blue-500">
                <span className="text-white">UI</span>
              </div>
              <span className="text-xl">UIWiki</span>
            </a>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-6">
              <a href="#components" className="text-gray-600 hover:text-gray-900 transition-colors">
                Components
              </a>
              <a href="#templates" className="text-gray-600 hover:text-gray-900 transition-colors">
                Templates
              </a>
              <a href="#examples" className="text-gray-600 hover:text-gray-900 transition-colors">
                Examples
              </a>
              <a href="#resources" className="text-gray-600 hover:text-gray-900 transition-colors">
                Resources
              </a>
            </nav>
          </div>

          {/* Search & Actions */}
          <div className="flex items-center gap-4">
            <div className="hidden lg:flex items-center relative">
              <Search className="absolute left-3 h-4 w-4 text-gray-400" />
              <Input
                type="search"
                placeholder="Search components..."
                className="pl-9 w-64 bg-gray-50 border-gray-200"
              />
            </div>
            
            <Button variant="ghost" size="icon" className="hidden md:flex">
              <Github className="h-5 w-5" />
            </Button>
            
            <Button variant="ghost" size="icon" className="md:hidden">
              <Menu className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
