import { Facebook, Instagram, Linkedin, Youtube } from 'lucide-react';

export function DarkFooter() {
  return (
    <footer className="bg-black border-t border-gray-900">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-8 mb-12">
          {/* Brand */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-6">
              <div className="flex h-8 w-8 items-center justify-center rounded bg-lime-400">
                <span className="text-black">DH</span>
              </div>
              <span className="text-white">DesignHub</span>
            </div>
          </div>
          
          {/* Products */}
          <div>
            <h4 className="text-white mb-4">Products</h4>
            <ul className="space-y-3 text-sm">
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Pricing</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Features</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Documentation</a></li>
            </ul>
          </div>
          
          {/* Resources */}
          <div>
            <h4 className="text-white mb-4">Resources</h4>
            <ul className="space-y-3 text-sm">
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Community</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Terms of Service</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Report an Issue</a></li>
            </ul>
          </div>
          
          {/* About */}
          <div>
            <h4 className="text-white mb-4">About</h4>
            <ul className="space-y-3 text-sm">
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">About Us</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Careers</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Contact</a></li>
            </ul>
          </div>
          
          {/* Join the community */}
          <div>
            <h4 className="text-white mb-4">Join the community</h4>
            <p className="text-gray-400 text-sm mb-4">Follow us</p>
            <div className="flex items-center gap-3">
              <a href="#" className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-900 text-gray-400 hover:text-white hover:bg-gray-800 transition-colors">
                <Facebook className="h-4 w-4" />
              </a>
              <a href="#" className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-900 text-gray-400 hover:text-white hover:bg-gray-800 transition-colors">
                <Instagram className="h-4 w-4" />
              </a>
              <a href="#" className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-900 text-gray-400 hover:text-white hover:bg-gray-800 transition-colors">
                <Linkedin className="h-4 w-4" />
              </a>
              <a href="#" className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-900 text-gray-400 hover:text-white hover:bg-gray-800 transition-colors">
                <Youtube className="h-4 w-4" />
              </a>
            </div>
          </div>
        </div>
        
        {/* Large Brand Text */}
        <div className="text-center opacity-5">
          <div className="text-9xl text-white tracking-wider select-none pointer-events-none">
            designhub
          </div>
        </div>
      </div>
    </footer>
  );
}
