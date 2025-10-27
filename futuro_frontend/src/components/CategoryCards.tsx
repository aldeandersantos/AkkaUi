import { Card } from './ui/card';

export function CategoryCards() {
  return (
    <section className="bg-black py-12">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          {/* UI-uowire Card */}
          <Card className="bg-gray-900 border-gray-800 hover:border-gray-700 transition-colors cursor-pointer overflow-hidden">
            <div className="aspect-[16/10] bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
              <div className="text-center">
                <div className="inline-flex h-16 w-16 items-center justify-center rounded-lg bg-gray-800 mb-3">
                  <svg className="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1v-3z" />
                  </svg>
                </div>
              </div>
            </div>
            <div className="p-4 text-center">
              <h3 className="text-white">UI-uowire</h3>
            </div>
          </Card>

          {/* Figma Card */}
          <Card className="bg-gray-900 border-gray-800 hover:border-gray-700 transition-colors cursor-pointer overflow-hidden">
            <div className="aspect-[16/10] bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
              <div className="text-center">
                <div className="inline-flex h-16 w-16 items-center justify-center rounded-lg bg-gray-800 mb-3">
                  <svg className="h-8 w-8 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 2C6.34 2 5 3.34 5 5s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3zm8 0C14.34 2 13 3.34 13 5s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3zM8 22c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm0-8c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm8 0c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"/>
                  </svg>
                </div>
              </div>
            </div>
            <div className="p-4 text-center">
              <h3 className="text-white">Figma</h3>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
