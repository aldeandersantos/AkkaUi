import { 
  Layout, 
  Type, 
  MousePointer2, 
  Menu, 
  Table, 
  Calendar,
  AlertCircle,
  CheckSquare,
  Square,
  FileText,
  BarChart3,
  Bell,
  MessageSquare,
  Image,
  Layers,
  Palette
} from 'lucide-react';
import { Card } from './ui/card';

const categories = [
  {
    icon: Layout,
    title: 'Layout',
    description: 'Grids, containers, and spacing utilities',
    count: '150+',
    color: 'from-blue-500 to-cyan-500'
  },
  {
    icon: MousePointer2,
    title: 'Buttons',
    description: 'Action buttons, links, and toggles',
    count: '80+',
    color: 'from-purple-500 to-pink-500'
  },
  {
    icon: Type,
    title: 'Typography',
    description: 'Headings, paragraphs, and text styles',
    count: '60+',
    color: 'from-orange-500 to-red-500'
  },
  {
    icon: Menu,
    title: 'Navigation',
    description: 'Navbars, menus, and breadcrumbs',
    count: '120+',
    color: 'from-green-500 to-emerald-500'
  },
  {
    icon: Table,
    title: 'Tables',
    description: 'Data tables and grid layouts',
    count: '90+',
    color: 'from-violet-500 to-purple-500'
  },
  {
    icon: Calendar,
    title: 'Forms',
    description: 'Inputs, selects, and form controls',
    count: '200+',
    color: 'from-pink-500 to-rose-500'
  },
  {
    icon: AlertCircle,
    title: 'Alerts',
    description: 'Notifications and messages',
    count: '50+',
    color: 'from-yellow-500 to-orange-500'
  },
  {
    icon: CheckSquare,
    title: 'Cards',
    description: 'Card components and containers',
    count: '180+',
    color: 'from-teal-500 to-cyan-500'
  },
  {
    icon: Square,
    title: 'Modals',
    description: 'Dialogs, drawers, and overlays',
    count: '70+',
    color: 'from-indigo-500 to-blue-500'
  },
  {
    icon: FileText,
    title: 'Content',
    description: 'Articles, blogs, and rich text',
    count: '100+',
    color: 'from-cyan-500 to-blue-500'
  },
  {
    icon: BarChart3,
    title: 'Charts',
    description: 'Data visualization components',
    count: '65+',
    color: 'from-blue-500 to-indigo-500'
  },
  {
    icon: Bell,
    title: 'Badges',
    description: 'Labels, tags, and indicators',
    count: '55+',
    color: 'from-purple-500 to-violet-500'
  },
  {
    icon: MessageSquare,
    title: 'Chat',
    description: 'Chat interfaces and messaging',
    count: '85+',
    color: 'from-green-500 to-teal-500'
  },
  {
    icon: Image,
    title: 'Media',
    description: 'Images, videos, and galleries',
    count: '110+',
    color: 'from-rose-500 to-pink-500'
  },
  {
    icon: Layers,
    title: 'Overlays',
    description: 'Tooltips, popovers, and dropdowns',
    count: '95+',
    color: 'from-amber-500 to-yellow-500'
  },
  {
    icon: Palette,
    title: 'Themes',
    description: 'Color schemes and dark mode',
    count: '40+',
    color: 'from-fuchsia-500 to-purple-500'
  }
];

export function ComponentShowcase() {
  return (
    <section className="py-20 bg-white">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="mb-4">Explore Components</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Browse our extensive library of UI components, organized by category. 
            Each component is fully customizable and production-ready.
          </p>
        </div>
        
        {/* Component Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {categories.map((category, index) => {
            const Icon = category.icon;
            return (
              <Card 
                key={index}
                className="group relative overflow-hidden border border-gray-200 hover:border-purple-300 hover:shadow-lg transition-all duration-300 cursor-pointer"
              >
                <div className="p-6">
                  {/* Icon */}
                  <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br ${category.color} opacity-90 group-hover:opacity-100 transition-opacity`}>
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  
                  {/* Content */}
                  <h3 className="mb-2">{category.title}</h3>
                  <p className="text-sm text-gray-600 mb-4">{category.description}</p>
                  
                  {/* Count Badge */}
                  <div className="inline-flex items-center gap-1 text-sm text-purple-600">
                    <span>{category.count} components</span>
                  </div>
                </div>
                
                {/* Hover Effect */}
                <div className={`absolute inset-0 bg-gradient-to-br ${category.color} opacity-0 group-hover:opacity-5 transition-opacity`} />
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
