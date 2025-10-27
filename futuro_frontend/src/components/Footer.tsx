import { Github, Twitter, Youtube, Heart } from 'lucide-react';

export function Footer() {
  return (
    <footer className="border-t bg-white">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-purple-600 to-blue-500">
                <span className="text-white">UI</span>
              </div>
              <span className="text-xl">UIWiki</span>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Beautiful UI components for modern web applications.
            </p>
            <div className="flex items-center gap-3">
              <a href="#" className="text-gray-400 hover:text-gray-600 transition-colors">
                <Github className="h-5 w-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-gray-600 transition-colors">
                <Twitter className="h-5 w-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-gray-600 transition-colors">
                <Youtube className="h-5 w-5" />
              </a>
            </div>
          </div>
          
          {/* Product */}
          <div>
            <h4 className="mb-4">Product</h4>
            <ul className="space-y-3 text-sm">
              <li><a href="#" className="text-gray-600 hover:text-gray-900 transition-colors">Components</a></li>
              <li><a href="#" className="text-gray-600 hover:text-gray-900 transition-colors">Templates</a></li>
              <li><a href="#" className="text-gray-600 hover:text-gray-900 transition-colors">Examples</a></li>
              <li><a href="#" className="text-gray-600 hover:text-gray-900 transition-colors">Pricing</a></li>
            </ul>
          </div>
          
          {/* Resources */}
          <div>
            <h4 className="mb-4">Resources</h4>
            <ul className="space-y-3 text-sm">
              <li><a href="#" className="text-gray-600 hover:text-gray-900 transition-colors">Documentation</a></li>
              <li><a href="#" className="text-gray-600 hover:text-gray-900 transition-colors">Guides</a></li>
              <li><a href="#" className="text-gray-600 hover:text-gray-900 transition-colors">Blog</a></li>
              <li><a href="#" className="text-gray-600 hover:text-gray-900 transition-colors">Changelog</a></li>
            </ul>
          </div>
          
          {/* Company */}
          <div>
            <h4 className="mb-4">Company</h4>
            <ul className="space-y-3 text-sm">
              <li><a href="#" className="text-gray-600 hover:text-gray-900 transition-colors">About</a></li>
              <li><a href="#" className="text-gray-600 hover:text-gray-900 transition-colors">Careers</a></li>
              <li><a href="#" className="text-gray-600 hover:text-gray-900 transition-colors">Contact</a></li>
              <li><a href="#" className="text-gray-600 hover:text-gray-900 transition-colors">Support</a></li>
            </ul>
          </div>
        </div>
        
        {/* Bottom Bar */}
        <div className="border-t pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-600">
            © 2025 UIWiki. All rights reserved.
          </p>
          <div className="flex items-center gap-1 text-sm text-gray-600">
            <span>Made with</span>
            <Heart className="h-4 w-4 text-red-500 fill-current" />
            <span>for the community</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
