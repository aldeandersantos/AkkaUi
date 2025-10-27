import { ImageWithFallback } from './figma/ImageWithFallback';
import { Card } from './ui/card';
import { Badge } from './ui/badge';

interface DesignItem {
  id: number;
  title: string;
  author: string;
  imageUrl: string;
  isFree: boolean;
}

const latestFigmaDesigns: DesignItem[] = [
  {
    id: 1,
    title: 'Furniture E-com',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1658297063569-162817482fb6?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 2,
    title: 'Agency Website',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1481487196290-c152efe083f5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 3,
    title: 'E-shop',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1453928582365-b6ad33cbcf64?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 4,
    title: 'Fintech',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1653307986572-d0176190386d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 5,
    title: 'Dashboard X',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1757310998437-b2e8a7bd2e97?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 6,
    title: 'Shop Now',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1658297063569-162817482fb6?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 7,
    title: 'Portfolio Pro',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1481487196290-c152efe083f5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 8,
    title: 'Saas Kit',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1609921212029-bb5a28e60960?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  }
];

interface DesignGridProps {
  title: string;
  designs?: DesignItem[];
}

export function DesignGrid({ title, designs = latestFigmaDesigns }: DesignGridProps) {
  return (
    <section className="bg-black py-16">
      <div className="container mx-auto px-4">
        {/* Section Title */}
        <h2 className="text-white mb-8 text-center">{title}</h2>
        
        {/* Design Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {designs.map((design) => (
            <Card 
              key={design.id}
              className="bg-gray-900 border-gray-800 hover:border-gray-700 transition-all duration-300 cursor-pointer group overflow-hidden"
            >
              {/* Image Preview */}
              <div className="aspect-[4/3] overflow-hidden bg-gray-800">
                <ImageWithFallback
                  src={design.imageUrl}
                  alt={design.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              </div>
              
              {/* Content */}
              <div className="p-4">
                <h3 className="text-white mb-1">{design.title}</h3>
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-400">{design.author}</p>
                  {design.isFree && (
                    <Badge className="bg-lime-400 text-black hover:bg-lime-500 px-2 py-0.5">
                      Free
                    </Badge>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
        
        {/* See More Button */}
        <div className="text-center">
          <button className="px-8 py-3 bg-lime-400 hover:bg-lime-500 text-black rounded-full transition-colors">
            See more
          </button>
        </div>
      </div>
    </section>
  );
}
