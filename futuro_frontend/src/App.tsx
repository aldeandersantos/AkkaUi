import { DarkHeader } from './components/DarkHeader';
import { DarkHero } from './components/DarkHero';
import { CategoryCards } from './components/CategoryCards';
import { DesignGrid } from './components/DesignGrid';
import { CommunityCTA } from './components/CommunityCTA';
import { DarkFooter } from './components/DarkFooter';

const componentDesigns = [
  {
    id: 1,
    title: 'The Greater Than To Shop',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1653307986572-d0176190386d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 2,
    title: 'Teach How-to-Use',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1609921212029-bb5a28e60960?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 3,
    title: 'Product Showcase',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1658297063569-162817482fb6?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 4,
    title: 'Pro Ecom',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1453928582365-b6ad33cbcf64?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 5,
    title: 'Header X',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1757310998437-b2e8a7bd2e97?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 6,
    title: 'Bios XL',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1481487196290-c152efe083f5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 7,
    title: 'FAQ Pro',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1653307986572-d0176190386d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  },
  {
    id: 8,
    title: 'CTA Collection',
    author: 'by UIwire UI',
    imageUrl: 'https://images.unsplash.com/photo-1609921212029-bb5a28e60960?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=600',
    isFree: true
  }
];

export default function App() {
  return (
    <div className="min-h-screen bg-black">
      <DarkHeader />
      <main>
        <DarkHero />
        <CategoryCards />
        <DesignGrid title="Latest Components" designs={componentDesigns} />
        <CommunityCTA />
      </main>
      <DarkFooter />
    </div>
  );
}
